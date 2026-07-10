# Import necessary modules
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages

# Create the state class
class AgentState(TypedDict):
    risk_score: float
    shap_features: dict
    retrieved_chunks: list
    red_flag: Literal["none", "advice", "urgent", "emergency"]
    summary: str
    messages: Annotated[list, add_messages]