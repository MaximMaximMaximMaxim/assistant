from langgraph import Node


@Node
def planner_node(state):
    """
    Generate a query plan based on the manager's question and any previous results.
    """
    