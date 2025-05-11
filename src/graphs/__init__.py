from graphs.fren.graph import graph as fren_graph
from graphs.echobot.graph import graph as echobot_graph


all_graphs = [
    {"id": "fren", "name": "🐸"},
    {"id": "echobot", "name": "EchoBot"}
]

# Dictionary to easily access graphs by ID
graph_registry = {
    "fren": fren_graph,
    "echobot": echobot_graph
}
