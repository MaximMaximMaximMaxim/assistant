from app.graph.builder import build_graph
from app.schemas import ChatMessage


async def run_graph(request: list[ChatMessage], context: dict):
    graph = build_graph()
    messages = [message.model_dump() for message in request]
    initial_state = {
        "messages": messages,
        "iteration": 0,
        "request_history": [],
        "responses": [],
        "errors": [],
        "context": context,
    }
    return await graph.ainvoke(initial_state)
