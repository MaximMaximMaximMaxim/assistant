Analytics Agent

Minimal FastAPI-based agent that receives manager requests, queries an analytics REST API, and summarizes findings using OpenRouter. Designed with separation of responsibilities: planner, executor, analyst.

Run locally with Docker Compose (see `.env.example`).

Endpoints:
- `POST /analyze` — accept manager request and return conclusions.

Environment variables (see `.env.example`):
- `ANALYTICS_API_URL` — base URL of analytics REST API
- `OPENROUTER_API_KEY` — OpenRouter API key
- `OPENROUTER_MODEL` — model name to use (default in .env.example)

Quick start (with Docker):
```
cp .env.example .env
# edit .env and set keys
docker compose up --build
```
