def route_after_evaluation(state) -> str:
    return "continue" if state.get("should_continue") else "finish"
