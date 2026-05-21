from app.clients.analytics import AnalyticsClient
from app.settings.config import settings


async def analytics_node(state):
    """Выполнить запрос к аналитическому API."""
    current_request = state.get("current_request") or {}
    endpoint = current_request.get("endpoint")
    params = current_request.get("params") or {}

    if not endpoint:
        errors = list(state.get("errors", []))
        errors.append("Не указан endpoint для выполнения запроса.")
        return {"errors": errors}

    client = AnalyticsClient(settings.analytics_base_url)

    try:
        data = await client.query(endpoint, params)
    except Exception as exc:  # noqa: BLE001
        errors = list(state.get("errors", []))
        errors.append(f"Ошибка запроса {endpoint}: {exc}")
        return {"errors": errors}

    responses = list(state.get("responses", []))
    responses.append({"endpoint": endpoint, "params": params, "data": data})

    return {"responses": responses}
