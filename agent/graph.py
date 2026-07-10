# Import necessary modules
from nodes import greet
from langgraph.graph import StateGraph
from state import AgentState
from langgraph.graph import START, END


# Create an empty graph
graph = StateGraph(AgentState)

# Design the "greet" node
graph.add_node("greet", greet)
graph.add_edge(START, "greet")
graph.add_edge("greet", END)
app = graph.compile()
result = app.invoke({"messages": []})
print(result)
