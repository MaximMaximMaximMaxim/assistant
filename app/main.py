from fastapi import FastAPI
from pydantic import BaseModel

from app.graph.runner import run_graph
from app.schemas import ChatMessage


app = FastAPI(title="Analytics TAO Agent")


@app.post("/analyze")
async def analyze(request: list[ChatMessage]):
    state = await run_graph(request, {})
    return {"result": state}