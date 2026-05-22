import httpx

from app.clients.analytics import AnalyticsClient
from app.settings.config import settings


async def analytics_node(state):
    """Выполнить запрос к аналитическому API."""
    current_request = state.get("current_request") or {}
    endpoint = current_request.get("endpoint")
    params = current_request.get("params")
    if params is None:
        params = {}

    if not endpoint:
        errors = list(state.get("errors", []))
        errors.append("Не указан endpoint для выполнения запроса.")
        return {"errors": errors}

    client = AnalyticsClient(settings.analytics_base_url)

    try:
        data = await client.query(endpoint, params)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        response_text = exc.response.text[:1000]
        if status_code in {400, 422}:
            api_error = {
                "endpoint": endpoint,
                "params": params,
                "status_code": status_code,
                "response": response_text,
            }
            request_history = list(state.get("request_history", []))
            if request_history:
                request_history[-1] = {
                    **request_history[-1],
                    "api_error": api_error,
                }
            print(f"API отклонил запрос: {api_error}")
            return {
                "last_api_error": api_error,
                "request_history": request_history,
                "request_valid": False,
            }

        errors = list(state.get("errors", []))
        errors.append(f"Ошибка запроса {endpoint}: {status_code} {response_text}")
        return {"errors": errors}
    except Exception as exc:  # noqa: BLE001
        errors = list(state.get("errors", []))
        errors.append(f"Ошибка запроса {endpoint}: {exc}")
        return {"errors": errors}

    responses = list(state.get("responses", []))
    responses.append({"endpoint": endpoint, "params": params, "data": data})

    return {"responses": responses, "last_api_error": None}
