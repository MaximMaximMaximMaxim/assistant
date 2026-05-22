from app.settings.config import settings


async def evaluator_node(state):
    """Определить, нужно ли продолжать цикл."""
    iteration = state.get("iteration", 0)
    analyst_report = state.get("analyst_report") or {}
    is_complete = analyst_report.get("is_complete")

    should_continue = False
    if is_complete is False:
        should_continue = True

    if iteration >= settings.max_iterations:
        should_continue = False

    if state.get("errors"):
        should_continue = False

    print(f"Оценщик определил, что цикл {'должен' if should_continue else 'не должен'} продолжаться")
    return {"should_continue": should_continue}
