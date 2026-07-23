# Import necessary modules
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


# Create the state class
class AgentState(TypedDict):
    patient_id: int
    risk_score: float
    retrieved_chunks: list
    red_flag: Literal["none", "advice", "urgent", "emergency"]
    outcome: Literal["escalate", "reassure", "followup", "human_handoff"]
    summary: str
    messages: Annotated[list, add_messages]
    followup_count: int
