# Import necessary modules
from agent.nodes import (
    greet,
    ask_followup,
    route_start,
    check_symptoms,
    route_severity,
    escalate, assess_risk,
    initial_state,
    reassure,
    summarize)
from langgraph.graph import StateGraph
from agent.state import AgentState
from langchain_core.messages import HumanMessage
from langgraph.graph import START, END


# Create an empty graph
graph = StateGraph(AgentState)

# Register all nodes
graph.add_node("greet", greet)
graph.add_node("ask_followup", ask_followup)
graph.add_node("check_symptoms", check_symptoms)
graph.add_node("escalate", escalate)
graph.add_node("assess_risk", assess_risk)
graph.add_node("reassure", reassure)
graph.add_node("summarize", summarize)

# Wire up edges
graph.add_conditional_edges(START, route_start)
graph.add_edge("greet", END)
graph.add_edge("check_symptoms", "assess_risk")
graph.add_conditional_edges("assess_risk", route_severity)
graph.add_edge("escalate", "summarize")
graph.add_edge("ask_followup", "summarize")
graph.add_edge("summarize", END)
graph.add_edge("reassure", END)


# Compile (last!)
app = graph.compile()

# Test
#result = app.invoke(initial_state(2, HumanMessage("I have fever and feeling shaky. My breath smells fruity")))
#print(result["messages"][-1].content)
