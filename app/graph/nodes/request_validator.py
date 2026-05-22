from app.graph.utils import validate_request_against_endpoints


async def request_validator_node(state):
    """Validate the planned API request before it reaches the analytics API."""
    current_request = state.get("current_request") or {}
    endpoint = current_request.get("endpoint")
    params = current_request.get("params")
    if params is None:
        params = {}
    endpoints = state.get("available_endpoints") or []

    normalized_params, validation_errors = validate_request_against_endpoints(
        endpoint,
        params,
        endpoints,
    )

    request_history = list(state.get("request_history", []))

    if validation_errors:
        rejected_request = {
            **current_request,
            "normalized_params": normalized_params,
        }
        if request_history:
            request_history[-1] = {
                **request_history[-1],
                "normalized_params": normalized_params,
                "validation_errors": validation_errors,
            }
        print(f"Валидатор отклонил запрос: {validation_errors}")
        return {
            "current_request": rejected_request,
            "request_history": request_history,
            "request_valid": False,
            "request_validation_errors": validation_errors,
        }

    normalized_request = {
        **current_request,
        "params": normalized_params,
    }
    if request_history:
        request_history[-1] = {
            **request_history[-1],
            "params": normalized_params,
            "validation_errors": [],
        }

    print(
        "Валидатор принял запрос: "
        f"{normalized_request.get('endpoint')} с params {normalized_params}"
    )
    return {
        "current_request": normalized_request,
        "request_history": request_history,
        "request_valid": True,
        "request_validation_errors": [],
    }
