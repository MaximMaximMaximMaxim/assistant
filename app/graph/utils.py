from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any


def get_last_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def extract_endpoints(openapi: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    paths = openapi.get("paths", {}) or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.lower() != "get":
                continue
            params = []
            for param in details.get("parameters", []) or []:
                params.append(
                    {
                        "name": param.get("name"),
                        "in": param.get("in"),
                        "required": param.get("required", False),
                        "schema": param.get("schema", {}),
                        "description": param.get("description", ""),
                    }
                )
            endpoints.append(
                {
                    "path": path,
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": params,
                }
            )
    return sorted(endpoints, key=lambda item: item["path"])


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def summarize_response(data: Any) -> str:
    if data is None:
        return "Пустой ответ."

    if isinstance(data, list):
        if not data:
            return "Пустой список данных."
        sample = data[0]
        summary = f"Список из {len(data)} элементов."
        if isinstance(sample, dict):
            keys = list(sample.keys())
            summary += f" Ключи первого элемента: {', '.join(keys[:8])}."
            if "created_at" in sample:
                created_dates = [
                    _parse_iso_date(item.get("created_at"))
                    for item in data
                    if isinstance(item, dict)
                ]
                created_dates = [d for d in created_dates if d]
                if created_dates:
                    summary += f" Диапазон created_at: {min(created_dates).date()} — {max(created_dates).date()}."
            if "completed_at" in sample:
                completed_dates = [
                    _parse_iso_date(item.get("completed_at"))
                    for item in data
                    if isinstance(item, dict)
                ]
                completed_dates = [d for d in completed_dates if d]
                if completed_dates:
                    summary += f" Диапазон completed_at: {min(completed_dates).date()} — {max(completed_dates).date()}."
        return summary

    if isinstance(data, dict):
        keys = list(data.keys())
        summary = f"Объект с ключами: {', '.join(keys[:10])}."
        numeric_parts = []
        nested_parts = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                numeric_parts.append(f"{key}={value}")
            elif isinstance(value, dict) and len(value) <= 10:
                nested_parts.append(f"{key}={value}")
        if numeric_parts:
            summary += " Числовые поля: " + ", ".join(numeric_parts[:8]) + "."
        if nested_parts:
            summary += " Вложенные значения: " + ", ".join(nested_parts[:5]) + "."
        return summary

    return "Неизвестный формат ответа."


def compute_daily_counts(
    items: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        date_value = _parse_iso_date(item.get(field))
        if date_value:
            counter[str(date_value.date())] += 1
    return [
        {"дата": date, "количество": count} for date, count in sorted(counter.items())
    ]


def derive_metrics(responses: list[dict[str, Any]]) -> dict[str, Any]:
    derived: dict[str, Any] = {}
    for response in responses:
        endpoint = response.get("endpoint", "")
        data = response.get("data")
        if endpoint.startswith("/tasks") and isinstance(data, list):
            derived["всего_задач"] = len(data)
            derived["приход_по_дням"] = compute_daily_counts(data, "created_at")
            derived["завершение_по_дням"] = compute_daily_counts(data, "completed_at")

            created_dates = [
                _parse_iso_date(item.get("created_at"))
                for item in data
                if isinstance(item, dict)
            ]
            created_dates = [d for d in created_dates if d]
            if created_dates:
                derived["диапазон_создания"] = {
                    "от": str(min(created_dates).date()),
                    "до": str(max(created_dates).date()),
                }

            completed_dates = [
                _parse_iso_date(item.get("completed_at"))
                for item in data
                if isinstance(item, dict)
            ]
            completed_dates = [d for d in completed_dates if d]
            if completed_dates:
                derived["диапазон_завершения"] = {
                    "от": str(min(completed_dates).date()),
                    "до": str(max(completed_dates).date()),
                }

    return derived
