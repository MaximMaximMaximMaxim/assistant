from app.settings.config import settings


def route_after_evaluation(state) -> str:
    return "continue" if state.get("should_continue") else "finish"


def route_after_planner(state) -> str:
    if state.get("errors"):
        return "finish"
    if state.get("current_request"):
        return "continue"
    return "finish"


def route_after_request_validation(state) -> str:
    if state.get("errors"):
        return "finish"
    if state.get("request_valid"):
        return "continue"
    if state.get("iteration", 0) >= settings.max_iterations:
        return "finish"
    return "repair"


def route_after_analytics(state) -> str:
    if state.get("errors"):
        return "finish"
    if state.get("last_api_error"):
        if state.get("iteration", 0) >= settings.max_iterations:
            return "finish"
        return "repair"
    return "continue"
