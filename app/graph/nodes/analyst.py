import json

from app.graph.utils import summarize_response
from app.llm import complete_json
from models.analyst_report import AnalystReport
import datetime


async def analyst_node(state):
    """Оценить достаточность данных и при необходимости запросить дополнительные."""
    last_user_message = ""
    for message in reversed(state.get("messages", [])):
        if message.get("role") == "user":
            last_user_message = message.get("content", "")
            break

    latest_response = None
    if state.get("responses"):
        latest_response = state.get("responses")[-1]

    response_summary = {}
    if latest_response:
        response_summary = {
            "endpoint": latest_response.get("endpoint"),
            "params": latest_response.get("params"),
            "summary": summarize_response(latest_response.get("data")),
        }

    system_prompt = (
        "Сегодня " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ". "
        "Ты аналитик. Тебе дан запрос менеджера и полученные данные. "
        "Определи, достаточно ли данных для ответа. "
        "Если данных недостаточно, перечисли, чего не хватает. "
        "Ответ строго JSON по схеме: "
        '{"is_complete": true/false, "missing_info": [..], "analysis": "..."}. '
        "Все тексты на русском."
    )

    user_payload = {
        "запрос_менеджера": last_user_message,
        "последний_ответ": response_summary,
        "все_ответы": [
            {
                "endpoint": response.get("endpoint"),
                "params": response.get("params"),
                "summary": summarize_response(response.get("data")),
            }
            for response in state.get("responses", [])
        ],
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    try:
        data = await complete_json(messages, temperature=0.1)
        report = AnalystReport(**data)
    except Exception as exc:  # noqa: BLE001
        errors = list(state.get("errors", []))
        errors.append(f"Ошибка анализа: {exc}")
        return {"errors": errors}

    print(f"Аналитик сформировал отчет: {report}")
    return {"analyst_report": report.model_dump()}
