import json

from app.clients.analytics import AnalyticsClient
from app.graph.utils import extract_endpoints, get_last_user_message, summarize_response
from app.llm import complete_json
from app.settings.config import settings
from models.api_query import AnalyticsQuery

import datetime


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
    validation_errors = state.get("request_validation_errors", [])
    last_api_error = state.get("last_api_error")
    failed_request = state.get("current_request", {}) if validation_errors or last_api_error else {}

    system_prompt = (
        "Сегодня " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ". "
        "Ты планировщик аналитического ассистента. "
        "На основе запроса менеджера и доступных эндпоинтов "
        "выбери один GET-запрос к API. Используй только эндпоинты из списка. "
        "Сначала сформулируй reasoning, потом выбери endpoint и params. "
        "Если переданы ошибки валидации или ошибка API, исправь предыдущий запрос с учетом этих ошибок. "
        "Если нужен период, используй start/end в ISO 8601. "
        "Если требуется разбивка по дням или сырые данные, "
        "допускается запрос /tasks/ и последующая агрегация. "
        "Пиши reasoning по-русски. Все текстовые поля — на русском. "
        "params всегда объект; если параметров нет, используй {}. "
        "Ответ строго JSON по схеме: "
        '{"reasoning": "...", "endpoint": "/path", "params": {..}}'
    )

    user_payload = {
        "запрос_менеджера": last_user_message,
        "доступные_эндпоинты": endpoints,
        "предыдущие_результаты": previous_results,
        "недостающая_информация": analyst_report.get("missing_info", []),
        "предыдущий_неудачный_запрос": failed_request,
        "ошибки_валидации_предыдущего_запроса": validation_errors,
        "ошибка_api_предыдущего_запроса": last_api_error,
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
    normalized_endpoint = endpoint.rstrip("/")
    for path in available_paths:
        if path.rstrip("/") == normalized_endpoint:
            endpoint = path
            break

    params = query.params or {}

    request_history = list(state.get("request_history", []))
    request_history.append(
        {
            "reasoning": query.reasoning,
            "endpoint": endpoint,
            "params": params,
        }
    )

    res = {
        "iteration": iteration,
        "openapi": openapi,
        "available_endpoints": endpoints,
        "current_request": {
            "reasoning": query.reasoning,
            "endpoint": endpoint,
            "params": params,
        },
        "request_history": request_history,
        "request_valid": False,
        "request_validation_errors": [],
        "last_api_error": None,
    }

    print(f"Планировщик выбрал запрос: {endpoint} с params {params}")
    print(res)
    return res
