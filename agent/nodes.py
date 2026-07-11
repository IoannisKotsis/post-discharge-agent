# Import necessary modules
from agent.state import AgentState
from langchain_core.messages import AIMessage
from rag.retriever import retrieve
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

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
        return "ask_followup"