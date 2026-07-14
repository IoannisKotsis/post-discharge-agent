# Import necessary module
from agent.graph import app

# Print the flow diagram
print(app.get_graph().draw_mermaid())