# Import necessary modules
from agent.nodes import greet, ask_followup, route_start,check_symptoms, route_severity, escalate
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


# Wire up edges
graph.add_conditional_edges(START, route_start)
graph.add_edge("greet", END)
graph.add_conditional_edges("check_symptoms", route_severity )
graph.add_edge("escalate", END)
graph.add_edge("ask_followup", END)


# Compile (last!)
app = graph.compile()

# Test
result = app.invoke({"messages": [HumanMessage("I'm confused, breathing fast, and my breath smells fruity")]})
print(result["messages"][-1].content)