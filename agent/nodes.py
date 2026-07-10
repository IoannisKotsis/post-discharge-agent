# Import necessary modules
from state import AgentState
from langchain_core.messages import AIMessage

def greet(state: AgentState):
    greeting = AIMessage("Hello, how are you feeling today?")
    return {"messages": [greeting]}
    