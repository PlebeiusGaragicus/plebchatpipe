from graphs.echobot import graph as echobot_graph
from graphs.example import graph as example_graph
from graphs.fren import graph as fren_graph
from graphs.research import graph as research_graph


all_graphs = [
    {"id": "echobot", "name": "EchoBot"},
    {"id": "example", "name": "Example"},
    {"id": "fren", "name": "🐸"},
    {"id": "research", "name": "🔍 Research"}
]

# Dictionary to easily access graphs by ID
graph_registry = {
    # id      # compiled_graph
    "echobot": echobot_graph,
    "example": example_graph,
    "fren": fren_graph,
    "research": research_graph
}
