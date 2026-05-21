from app.schemas import ChatMessage
from app.graph.builder import build_graph


def run_graph(request: list[ChatMessage], context: dict):
    graph = build_graph()
    return graph.run(request, context)