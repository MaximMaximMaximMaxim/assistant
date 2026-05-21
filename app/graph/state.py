from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    iteration: int
    openapi: dict[str, Any]
    available_endpoints: list[dict[str, Any]]
    current_request: dict[str, Any]
    request_history: list[dict[str, Any]]
    responses: list[dict[str, Any]]
    analyst_report: dict[str, Any]
    should_continue: bool
    final_answer: str
    errors: list[str]
    context: dict[str, Any]
