from fastapi import FastAPI

from app.graph.runner import run_graph
from app.schemas import ChatMessage

app = FastAPI(title="Analytics TAO Agent")


@app.post("/analyze")
async def analyze(request: list[ChatMessage]):
    state = await run_graph(request, {})
    return {"answer": state.get("final_answer", ""), "errors": state.get("errors", [])}
