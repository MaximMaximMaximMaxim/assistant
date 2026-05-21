import json
from typing import Any

from app.clients.openrouter import client
from app.settings.config import settings


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


async def complete_json(
    messages: list[dict[str, str]], temperature: float = 0.2
) -> dict[str, Any]:
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    data = _extract_json(content)
    if data is None:
        raise ValueError("Не удалось разобрать JSON из ответа модели.")
    return data


async def complete_text(
    messages: list[dict[str, str]], temperature: float = 0.3
) -> str:
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""
