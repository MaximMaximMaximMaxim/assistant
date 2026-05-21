import json

from app.clients.analytics import AnalyticsClient
from app.graph.utils import extract_endpoints, get_last_user_message, summarize_response
from app.llm import complete_json
from app.settings.config import settings
from models.api_query import AnalyticsQuery


async def planner_node(state):
    """Сформировать следующий запрос к аналитическому API на основе сообщения менеджера."""
    iteration = state.get("iteration", 0) + 1

    openapi = state.get("openapi")
    if openapi is None:
        client = AnalyticsClient(settings.analytics_base_url)
        try:
            openapi = await client.query("/openapi.json", {})
        except Exception as exc:  # noqa: BLE001
            errors = list(state.get("errors", []))
            errors.append(f"Ошибка получения openapi: {exc}")
            return {"errors": errors}

    endpoints = state.get("available_endpoints") or extract_endpoints(openapi)

    last_user_message = get_last_user_message(state.get("messages", []))

    previous_results = []
    for response in state.get("responses", []):
        previous_results.append(
            {
                "endpoint": response.get("endpoint"),
                "params": response.get("params"),
                "summary": summarize_response(response.get("data")),
            }
        )

    analyst_report = state.get("analyst_report") or {}

    system_prompt = (
        "Ты планировщик аналитического ассистента. "
        "На основе запроса менеджера и доступных эндпоинтов "
        "выбери один GET-запрос к API. Используй только эндпоинты из списка. "
        "Если нужен период, используй start/end в ISO 8601. "
        "Если требуется разбивка по дням или сырые данные, "
        "допускается запрос /tasks/ и последующая агрегация. "
        "Пиши reasoning по-русски. Все текстовые поля — на русском. "
        "params всегда объект; если параметров нет, используй {}. "
        "Ответ строго JSON по схеме: "
        '{"endpoint": "/path", "params": {..}, "reasoning": "..."}'
    )

    user_payload = {
        "запрос_менеджера": last_user_message,
        "доступные_эндпоинты": endpoints,
        "предыдущие_результаты": previous_results,
        "недостающая_информация": analyst_report.get("missing_info", []),
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    try:
        data = await complete_json(messages, temperature=0.1)
        query = AnalyticsQuery(**data)
    except Exception as exc:  # noqa: BLE001
        errors = list(state.get("errors", []))
        errors.append(f"Ошибка планирования: {exc}")
        return {"errors": errors}

    endpoint = query.endpoint
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    available_paths = [item.get("path", "") for item in endpoints]
    normalized_paths = {path.rstrip("/") for path in available_paths if path}
    normalized_endpoint = endpoint.rstrip("/")
    if normalized_endpoint not in normalized_paths:
        errors = list(state.get("errors", []))
        errors.append(f"Планировщик выбрал неизвестный endpoint: {endpoint}")
        return {"errors": errors}

    for path in available_paths:
        if path.rstrip("/") == normalized_endpoint:
            endpoint = path
            break

    params = query.params or {}

    request_history = list(state.get("request_history", []))
    request_history.append(
        {
            "endpoint": endpoint,
            "params": params,
            "reasoning": query.reasoning,
        }
    )

    return {
        "iteration": iteration,
        "openapi": openapi,
        "available_endpoints": endpoints,
        "current_request": {"endpoint": endpoint, "params": params},
        "request_history": request_history,
    }
