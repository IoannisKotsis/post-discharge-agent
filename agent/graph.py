# Import necessary modules
from agent.nodes import greet, ask_followup, route_start
from langgraph.graph import StateGraph
from agent.state import AgentState
from langgraph.graph import START, END


# Create an empty graph
graph = StateGraph(AgentState)

# Register all nodes
graph.add_node("greet", greet)
graph.add_node("ask_followup", ask_followup)

# Wire up edges
graph.add_conditional_edges(START, route_start)
graph.add_edge("greet", END)
graph.add_edge("ask_followup", END)


# Compile (last!)
app = graph.compile()

# Test
result = app.invoke({"messages": []})
print(result)