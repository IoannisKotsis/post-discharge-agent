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
    greeting = AIMessage("Hello, how are you feeling today?")
    return {"messages": [greeting]}
    
# Ask followup
def ask_followup(state: AgentState):
    patient_message = state["messages"][-1].content
    retrieved = retrieve(patient_message)
    
    context = ""
    for chunk in retrieved:
        context += f"{chunk['text']}\n"
        
    response = llm.invoke([
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(f"Patient said: {patient_message}\n\nRelevant guidelines:\n{context}")      
    ])
            
    return {"retrieved_chunks": retrieved, "messages": [response]}

# Decide entry point: greet if conversation just started, else answer the patient
def route_start(state: AgentState):
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
    patient_message = state["messages"][-1].content
    
    response = llm.invoke([
        SystemMessage(CLASSIFY_PROMPT),
        HumanMessage(f"Patient said: {patient_message}")      
    ])
    
    severity_levels = ["none", "advice", "urgent", "emergency"]
    symptoms_severity = "".join(c for c in (response.content).strip().lower() if c.isalpha())
    if symptoms_severity not in severity_levels:
        symptoms_severity = "advice"
        
    return {"red_flag": symptoms_severity}


# Decide severity: escalate if urgent/emergency , else ask follow-up question
HIGH_RISK_THRESHOLD = 0.7

def route_severity(state: AgentState):
    # Serious symptom always escalates — risk score cannot override
    if state["red_flag"] in ("urgent", "emergency"):
        return "escalate"
    # Mild symptom but high-risk patient → upgrade to escalate (score only raises, never lowers)
    risk = state["risk_score"]
    if risk is not None and risk >= HIGH_RISK_THRESHOLD:
        return "escalate"
    # Mild symptom, low risk → routine follow-up
    return "ask_followup"
    

# Escalate case
ESCALATE_PROMPT = """
You are a post-discharge assistant for diabetic patients and you are guiding the patient to care actions if the symptoms are severe.
You are reading their message and you are responding to them based on the severity (urgent or emergency).
For emergency, direct them to call emergency services immediately; for urgent, advise contacting their care team or attending A&E soon.
Use ONLY the guidelines provided below. If they don't cover the situation, tell the patient to seek professional help — do not invent medical advice.
Your talking tone is serious but calm, not panicky.
"""

def escalate(state: AgentState):
    patient_message = state["messages"][-1].content
    severity_level = state["red_flag"]
    
    try:
        retrieved = retrieve(patient_message)
    except Exception as e:
        print(f"Retrieval failed: {e}")
        retrieved = []
    
    if not retrieved:
        return {"messages": [AIMessage("Contact immediately a doctor or go to A&E.")]}
    
    context = "\n".join(chunk["text"] for chunk in retrieved)
    response = llm.invoke([
        SystemMessage(ESCALATE_PROMPT),
        HumanMessage(f"Patient said: {patient_message}\nSymptoms severity: {severity_level}\nRelevant guidelines:\n{context}")      
    ])
    
    return {"messages": [response]}


# Assess risk score from patient
def assess_risk(state: AgentState):
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
    return {
        "patient_id": patient_id,
        "risk_score": None,
        "red_flag": "none",
        "retrieved_chunks": [],
        "shap_features": {},
        "summary": "",
        "messages": [first_message],
    }



        
    