def route_after_evaluation(state) -> str:
    return "continue" if state.get("should_continue") else "finish"


def route_after_planner(state) -> str:
    if state.get("errors"):
        return "finish"
    if state.get("current_request"):
        return "continue"
    return "finish"
