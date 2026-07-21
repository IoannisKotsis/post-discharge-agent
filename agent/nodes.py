# Import necessary modules
from agent.state import AgentState
from langchain_core.messages import AIMessage
from rag.retriever import retrieve
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import requests

# Import environment variables from .env
load_dotenv()

# Create an LLM isntance
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Set the system prompt
SYSTEM_PROMPT = """
You are a post_discharge follow-up assistant for diabetic patients. You respond only based on the given guidelines
without making diagnoses or prescribing medication doses.If the guidelines don't cover the question,
say so honestly and suggest contacting their care team, rather than guessing. If you notice serious symptoms
then refer to a doctor. Ask a relevant follow-up question to continue checking on the patient's recovery.
You talk simply, with empathy and kindly.
"""


# Greeting
def greet(state: AgentState):
    """Return the opening message when a conversation starts."""
    greeting = AIMessage("Hello, how are you feeling today?")
    return {"messages": [greeting]}


# Ask followup
def ask_followup(state: AgentState):
    """Answer a mild-symptom message with RAG-grounded guidance and a follow-up question."""
    patient_message = state["messages"][-1].content
    retrieved = retrieve(patient_message)

    context = ""
    for chunk in retrieved:
        context += f"{chunk['text']}\n"

    response = llm.invoke(
        [
            SystemMessage(SYSTEM_PROMPT),
            HumanMessage(
                f"Patient said: {patient_message}\n\nRelevant guidelines:\n{context}"
            ),
        ]
    )

    return {
        "retrieved_chunks": retrieved,
        "messages": [response],
        "outcome": "followup",
    }


# Decide entry point: greet if conversation just started, else answer the patient
def route_start(state: AgentState):
    """Entry router: greet on an empty conversation, otherwise triage the message."""
    if len(state["messages"]) == 0:
        return "greet"
    else:
        return "check_symptoms"


# Decide the symptoms severity
CLASSIFY_PROMPT = """
You are a triage classifier for diabetic patients after discharge.
You read the patient's message and you respond ONLY with one word: none, advice, urgent, or emergency. No explanation.
The criterias are: 
    - emergency: DKA signs or life-threatening (fruity breath, confusion, difficulty breathing, high ketones...)
    - urgent: "call 999" cases / go to A&E (feeling very sick, drowsy, can't stay awake...)
    - advice: contact your doctor soon (symptoms that do not subside, mild but constant)
    - none: everything is fine, no need to worry
"""


def check_symptoms(state: AgentState):
    """Classify the patient's message into one of four severity levels; defaults to 'advice' if unparseable."""
    patient_message = state["messages"][-1].content

    response = llm.invoke(
        [
            SystemMessage(CLASSIFY_PROMPT),
            HumanMessage(f"Patient said: {patient_message}"),
        ]
    )

    severity_levels = ["none", "advice", "urgent", "emergency"]
    symptoms_severity = "".join(
        c for c in (response.content).strip().lower() if c.isalpha()
    )
    if symptoms_severity not in severity_levels:
        symptoms_severity = "advice"

    return {"red_flag": symptoms_severity}


# Decide severity: escalate if urgent/emergency , else ask follow-up question
HIGH_RISK_THRESHOLD = 0.7


def route_severity(state: AgentState):
    """Route to escalate/reassure/ask_followup. Risk score can only raise severity, never lower it."""
    # Serious symptom always escalates — risk score cannot override
    if state["red_flag"] in ("urgent", "emergency"):
        return "escalate"
    # Mild symptom but high-risk patient → upgrade to escalate (score only raises, never lowers)
    risk = state["risk_score"]
    if risk is not None and risk >= HIGH_RISK_THRESHOLD:
        return "escalate"
    # Mild symptom, low risk → routine follow-up
    if state["red_flag"] == "none":
        return "reassure"
    return "ask_followup"


# Escalate case
ESCALATE_PROMPT = """
You are a post-discharge assistant for diabetic patients and you are guiding the patient to care actions because the symptoms are severe.
You are reading their message and you are responding to them based on the severity (urgent or emergency). 
For emergency, direct them to call emergency services immediately; for urgent, advise contacting their care team or attending A&E soon.
If Readmsission risk is high (above 70%), escalate even if the symptoms seem mild. The high risk alone justifies the contact with a care team.
Use ONLY the guidelines provided below. If they don't cover the situation, tell the patient to seek professional help — do not invent medical advice.
Your talking tone is serious but calm, not panicky. Do not close with a question but give a clear response in total.
"""


def escalate(state: AgentState):
    """Direct the patient to urgent care, grounded in guidelines; falls back to a safe message if retrieval fails."""
    patient_message = state["messages"][-1].content
    severity_level = state["red_flag"]
    risk_score = state["risk_score"]

    try:
        retrieved = retrieve(patient_message)
    except Exception as e:
        print(f"Retrieval failed: {e}")
        retrieved = []

    if not retrieved:
        return {"messages": [AIMessage("Contact immediately a doctor or go to A&E.")]}

    context = "\n".join(chunk["text"] for chunk in retrieved)
    response = llm.invoke(
        [
            SystemMessage(ESCALATE_PROMPT),
            HumanMessage(
                f"Patient said: {patient_message}\nSymptoms severity: {severity_level}\nReadmission risk: {risk_score}\nRelevant guidelines:\n{context}"
            ),
        ]
    )

    return {"messages": [response], "outcome": "escalate"}


# Assess risk score from patient
def assess_risk(state: AgentState):
    """Fetch the patient's readmission risk from the prediction API; assumes maximum risk (1.0) on failure."""
    if state.get("risk_score") is not None:
        return {}
    patient_id = state["patient_id"]

    url = os.getenv("READMISSION_API_URL")
    final_url = f"{url}/risk/{patient_id}"

    try:
        response = requests.get(final_url)
        response.raise_for_status()
        data = response.json()
        risk_score = data["risk_score"]
    except Exception as e:
        print(f"Risk API failed: {e}")
        risk_score = 1

    return {"risk_score": float(risk_score)}


# Initial state fields
def initial_state(patient_id, first_message):
    """Build a fresh AgentState for a new conversation."""
    return {
        "patient_id": patient_id,
        "risk_score": None,
        "red_flag": "none",
        "retrieved_chunks": [],
        "summary": "",
        "messages": [first_message],
    }


# Reassure case
REASSURANCE_PROMPT = """
You are a post-discharge assistant for diabetic patients and trying to reassure them when their symptoms are not severe.
Use ONLY the guidelines provided below. If they don't cover the situation, tell the patient that you cannot offer a specific guidance and that they need to contact
their care team. Your talking tone is serious and calm. The goal is to comfort the patient and not make him have second thoughts about their symptoms.
Do not close your answer with a question.
"""


def reassure(state: AgentState):
    """Reassure the patient when symptoms are mild and risk is low, grounded in guidelines."""
    patient_message = state["messages"][-1].content

    try:
        retrieved = retrieve(patient_message)
    except Exception as e:
        print(f"Retrieval failed: {e}")
        retrieved = []

    if not retrieved:
        return {
            "messages": [
                AIMessage(
                    "Based on what you've described, this doesn't appear urgent, but contact your care team as I cannot guide you specifically at this point."
                )
            ]
        }

    context = "\n".join(chunk["text"] for chunk in retrieved)
    response = llm.invoke(
        [
            SystemMessage(REASSURANCE_PROMPT),
            HumanMessage(
                f"Patient said: {patient_message}\n\nRelevant guidelines:\n{context}"
            ),
        ]
    )

    return {"messages": [response], "outcome": "reassure"}


# Summarize conversation

SUMMARY_PROMPT = """
You are a post-discharge assistant for diabetic patients. You are reading the messages exchanged between the agent and the patient
and you give to the doctor a summary of this conversation, without adding additional information. The summary must include:
    - patient's symptoms
    - conversation outcome (escalation / advice)
The summary must be concise (2-3 sentences) in order for the doctor to scan it fast and understand the meaning easily.
Write in third person, with clinical style (e.g. the patient reported) and neutral tone.
"""


def summarize(state: AgentState):
    """Generate a clinical summary of the conversation and store it via the readmission API."""
    conversation = "\n".join(
        f"{type(m).__name__}: {m.content}" for m in state["messages"]
    )
    response = llm.invoke(
        [
            SystemMessage(SUMMARY_PROMPT),
            HumanMessage(f"Here is the conversation to summarize:\n\n{conversation}"),
        ]
    )
    summary = response.content

    patient_id = state["patient_id"]
    red_flag = state["red_flag"]
    url = os.getenv("READMISSION_API_URL")
    final_url = f"{url}/summary"

    try:
        r = requests.post(
            final_url,
            json={
                "patient_id": patient_id,
                "summary": summary,
                "final_red_flag": red_flag,
            },
        )
        r.raise_for_status()
    except Exception as e:
        print(f"Summary save failed: {e}")

    return {"summary": summary}
