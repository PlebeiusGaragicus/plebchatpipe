from graphs.echobot import graph as echobot_graph
# from graphs.fren import graph as fren_graph
# from graphs.research import graph as research_graph


all_graphs = [
    {"id": "echobot", "name": "EchoBot"},
    # {"id": "fren", "name": "🐸"},
    # {"id": "research", "name": "🔍 Research"}
]

# Dictionary to easily access graphs by ID
graph_registry = {
    "echobot": echobot_graph,
    # "fren": fren_graph,
    # "research": research_graph
}
