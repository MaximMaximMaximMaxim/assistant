from fastapi import FastAPI
import schemas


app = FastAPI()


@app.get("/chat")
async def chat(messages: list[schemas.ChatMessage]):
    ...