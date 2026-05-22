import datetime
import json

from app.graph.utils import derive_metrics, get_last_user_message, summarize_response
from app.llm import complete_text


async def generator_node(state):
    """Сформировать финальный ответ менеджеру на русском языке."""
    last_user_message = get_last_user_message(state.get("messages", []))

    responses = state.get("responses", [])
    derived = derive_metrics(responses)

    def _preview_data(data):
        if isinstance(data, dict) and len(data) <= 20:
            return data
        if isinstance(data, list):
            if len(data) <= 5:
                return data
            return data[:3]
        return None

    results_summary = []
    for response in responses:
        data = response.get("data")
        results_summary.append(
            {
                "endpoint": response.get("endpoint"),
                "params": response.get("params"),
                "summary": summarize_response(data),
                "preview": _preview_data(data),
            }
        )

    system_prompt = (
        "Сегодня " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ". "
        "Ты формируешь финальный ответ менеджеру. "
        "Используй только фактические данные из полученных результатов и производных метрик. "
        "Дай связный анализ с конкретными числами. "
        "Если данных недостаточно, скажи, чего не хватает. "
        "Пиши по-русски."
    )

    user_payload = {
        "запрос_менеджера": last_user_message,
        "сводка_ответов": results_summary,
        "производные_метрики": derived,
        "заметки_аналитика": state.get("analyst_report", {}),
        "ошибки": state.get("errors", []),
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    try:
        answer = await complete_text(messages, temperature=0.2)
    except Exception as exc:  # noqa: BLE001
        errors = list(state.get("errors", []))
        errors.append(f"Ошибка генерации ответа: {exc}")
        return {"errors": errors, "final_answer": ""}

    return {"final_answer": answer}
