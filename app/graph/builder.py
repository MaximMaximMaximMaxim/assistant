from langgraph.graph import END, StateGraph

from app.graph.edges.routing import route_after_analytics
from app.graph.edges.routing import route_after_evaluation
from app.graph.edges.routing import route_after_planner
from app.graph.edges.routing import route_after_request_validation
from app.graph.nodes.analyst import analyst_node
from app.graph.nodes.analytics_api import analytics_node
from app.graph.nodes.evaluator import evaluator_node
from app.graph.nodes.generator import generator_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.request_validator import request_validator_node
from app.graph.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("request_validator", request_validator_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("generator", generator_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "continue": "request_validator",
            "finish": "generator",
        },
    )
    graph.add_conditional_edges(
        "request_validator",
        route_after_request_validation,
        {
            "continue": "analytics",
            "repair": "planner",
            "finish": "generator",
        },
    )
    graph.add_conditional_edges(
        "analytics",
        route_after_analytics,
        {
            "continue": "analyst",
            "repair": "planner",
            "finish": "generator",
        },
    )
    graph.add_edge("analyst", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "continue": "planner",
            "finish": "generator",
        },
    )

    graph.add_edge("generator", END)

    return graph.compile()
