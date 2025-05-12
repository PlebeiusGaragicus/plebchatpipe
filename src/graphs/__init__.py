from graphs.fren import graph as fren_graph
from graphs.echobot import graph as echobot_graph
from graphs.research import graph as research_graph


all_graphs = [
    {"id": "fren", "name": "🐸"},
    {"id": "echobot", "name": "EchoBot"},
    {"id": "research", "name": "🔍 Research"}
]

# Dictionary to easily access graphs by ID
graph_registry = {
    "fren": fren_graph,
    "echobot": echobot_graph,
    "research": research_graph
}
