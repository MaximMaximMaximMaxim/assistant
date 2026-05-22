from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any


def get_last_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def extract_endpoints(openapi: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    paths = openapi.get("paths", {}) or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.lower() != "get":
                continue
            params = []
            for param in details.get("parameters", []) or []:
                params.append(
                    {
                        "name": param.get("name"),
                        "in": param.get("in"),
                        "required": param.get("required", False),
                        "schema": param.get("schema", {}),
                        "description": param.get("description", ""),
                    }
                )
            endpoints.append(
                {
                    "path": path,
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": params,
                }
            )
    return sorted(endpoints, key=lambda item: item["path"])


def _strip_null_schema_options(schema: dict[str, Any]) -> dict[str, Any]:
    for key in ("anyOf", "oneOf"):
        options = schema.get(key)
        if not isinstance(options, list):
            continue

        non_null_options = [
            option
            for option in options
            if isinstance(option, dict) and option.get("type") != "null"
        ]
        if len(non_null_options) == 1:
            merged = {**schema, **non_null_options[0]}
            merged.pop(key, None)
            return merged

    return schema


def _schema_type(schema: dict[str, Any]) -> str | None:
    schema = _strip_null_schema_options(schema)
    value = schema.get("type")
    if isinstance(value, list):
        non_null = [item for item in value if item != "null"]
        return non_null[0] if non_null else None
    if isinstance(value, str):
        return value
    if "enum" in schema:
        return "string"
    return None


def _is_empty_query_value(value: Any) -> bool:
    return value is None or value == "" or value == []


def _format_allowed_params(names: set[str]) -> str:
    return ", ".join(sorted(names)) if names else "нет query-параметров"


def _coerce_bool(value: Any) -> tuple[bool | None, str | None]:
    if isinstance(value, bool):
        return value, None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True, None
        if normalized in {"false", "0", "no", "n"}:
            return False, None
    return None, "ожидается boolean"


def _coerce_int(value: Any) -> tuple[int | None, str | None]:
    if isinstance(value, bool):
        return None, "ожидается integer"
    if isinstance(value, int):
        return value, None
    if isinstance(value, str):
        try:
            return int(value.strip()), None
        except ValueError:
            return None, "ожидается integer"
    return None, "ожидается integer"


def _coerce_float(value: Any) -> tuple[float | int | None, str | None]:
    if isinstance(value, bool):
        return None, "ожидается number"
    if isinstance(value, (int, float)):
        return value, None
    if isinstance(value, str):
        try:
            return float(value.strip()), None
        except ValueError:
            return None, "ожидается number"
    return None, "ожидается number"


def _validate_string_format(name: str, value: str, schema: dict[str, Any]) -> str | None:
    value_format = schema.get("format")
    if value_format == "date-time" and _parse_iso_date(value) is None:
        return f"параметр '{name}' должен быть ISO 8601 date-time"
    if value_format == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            return f"параметр '{name}' должен быть ISO 8601 date"
    return None


def _coerce_query_value(
    name: str,
    value: Any,
    schema: dict[str, Any],
) -> tuple[Any, list[str]]:
    schema = _strip_null_schema_options(schema or {})
    expected_type = _schema_type(schema)
    errors: list[str] = []

    if expected_type == "array":
        item_schema = _strip_null_schema_options(schema.get("items") or {})
        raw_items = value if isinstance(value, list) else [value]
        coerced_items = []
        for item in raw_items:
            coerced_item, item_errors = _coerce_query_value(name, item, item_schema)
            errors.extend(item_errors)
            if not item_errors:
                coerced_items.append(coerced_item)
        return coerced_items, errors

    if expected_type == "boolean":
        coerced, error = _coerce_bool(value)
    elif expected_type == "integer":
        coerced, error = _coerce_int(value)
    elif expected_type == "number":
        coerced, error = _coerce_float(value)
    elif expected_type == "string" or expected_type is None:
        if isinstance(value, (dict, list)):
            coerced, error = None, "ожидается строковое значение"
        else:
            coerced, error = str(value), None
    else:
        coerced, error = value, None

    if error:
        return value, [f"параметр '{name}': {error}"]

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and enum_values and coerced not in enum_values:
        return coerced, [
            f"параметр '{name}' должен быть одним из: {', '.join(map(str, enum_values))}"
        ]

    if isinstance(coerced, str):
        format_error = _validate_string_format(name, coerced, schema)
        if format_error:
            errors.append(format_error)

    return coerced, errors


def validate_request_against_endpoints(
    endpoint: str | None,
    params: Any,
    endpoints: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Validate and lightly normalize generated query params before the API call."""
    if not endpoint:
        return {}, ["Не указан endpoint для выполнения запроса."]

    normalized_endpoint = endpoint.rstrip("/")
    endpoint_details = next(
        (
            item
            for item in endpoints
            if str(item.get("path", "")).rstrip("/") == normalized_endpoint
        ),
        None,
    )
    if endpoint_details is None:
        return {}, [f"Неизвестный endpoint: {endpoint}"]

    errors: list[str] = []
    if "{" in endpoint or "}" in endpoint:
        errors.append(
            "endpoint содержит незаполненные path-параметры; выбери готовый путь без {param}"
        )

    if not isinstance(params, dict):
        return {}, ["params должен быть объектом."]

    query_specs = [
        param
        for param in endpoint_details.get("parameters", []) or []
        if param.get("in") == "query"
    ]
    specs_by_name = {
        str(param.get("name")): param
        for param in query_specs
        if param.get("name") is not None
    }
    allowed_names = set(specs_by_name)
    normalized_params: dict[str, Any] = {}
    empty_required_names: set[str] = set()

    for name, value in params.items():
        name = str(name)
        if name not in allowed_names:
            errors.append(
                f"неизвестный query-параметр '{name}' для {endpoint}. "
                f"Доступные параметры: {_format_allowed_params(allowed_names)}"
            )
            continue

        spec = specs_by_name[name]
        if _is_empty_query_value(value):
            if spec.get("required"):
                errors.append(f"обязательный query-параметр '{name}' не заполнен")
                empty_required_names.add(name)
            continue

        coerced, value_errors = _coerce_query_value(
            name,
            value,
            spec.get("schema") or {},
        )
        errors.extend(value_errors)
        if not value_errors:
            normalized_params[name] = coerced

    for name, spec in specs_by_name.items():
        if (
            spec.get("required")
            and name not in normalized_params
            and name not in empty_required_names
        ):
            errors.append(f"обязательный query-параметр '{name}' отсутствует")

    return normalized_params, errors


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def summarize_response(data: Any) -> str:
    if data is None:
        return "Пустой ответ."

    if isinstance(data, list):
        if not data:
            return "Пустой список данных."
        sample = data[0]
        summary = f"Список из {len(data)} элементов."
        if isinstance(sample, dict):
            keys = list(sample.keys())
            summary += f" Ключи первого элемента: {', '.join(keys[:8])}."
            if "created_at" in sample:
                created_dates = [
                    _parse_iso_date(item.get("created_at"))
                    for item in data
                    if isinstance(item, dict)
                ]
                created_dates = [d for d in created_dates if d]
                if created_dates:
                    summary += f" Диапазон created_at: {min(created_dates).date()} — {max(created_dates).date()}."
            if "completed_at" in sample:
                completed_dates = [
                    _parse_iso_date(item.get("completed_at"))
                    for item in data
                    if isinstance(item, dict)
                ]
                completed_dates = [d for d in completed_dates if d]
                if completed_dates:
                    summary += f" Диапазон completed_at: {min(completed_dates).date()} — {max(completed_dates).date()}."
        return summary

    if isinstance(data, dict):
        keys = list(data.keys())
        summary = f"Объект с ключами: {', '.join(keys[:10])}."
        numeric_parts = []
        nested_parts = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                numeric_parts.append(f"{key}={value}")
            elif isinstance(value, dict) and len(value) <= 10:
                nested_parts.append(f"{key}={value}")
        if numeric_parts:
            summary += " Числовые поля: " + ", ".join(numeric_parts[:8]) + "."
        if nested_parts:
            summary += " Вложенные значения: " + ", ".join(nested_parts[:5]) + "."
        return summary

    return "Неизвестный формат ответа."


def compute_daily_counts(
    items: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        date_value = _parse_iso_date(item.get(field))
        if date_value:
            counter[str(date_value.date())] += 1
    return [
        {"дата": date, "количество": count} for date, count in sorted(counter.items())
    ]


def derive_metrics(responses: list[dict[str, Any]]) -> dict[str, Any]:
    derived: dict[str, Any] = {}
    for response in responses:
        endpoint = response.get("endpoint", "")
        data = response.get("data")
        if endpoint.startswith("/tasks") and isinstance(data, list):
            derived["всего_задач"] = len(data)
            derived["приход_по_дням"] = compute_daily_counts(data, "created_at")
            derived["завершение_по_дням"] = compute_daily_counts(data, "completed_at")

            created_dates = [
                _parse_iso_date(item.get("created_at"))
                for item in data
                if isinstance(item, dict)
            ]
            created_dates = [d for d in created_dates if d]
            if created_dates:
                derived["диапазон_создания"] = {
                    "от": str(min(created_dates).date()),
                    "до": str(max(created_dates).date()),
                }

            completed_dates = [
                _parse_iso_date(item.get("completed_at"))
                for item in data
                if isinstance(item, dict)
            ]
            completed_dates = [d for d in completed_dates if d]
            if completed_dates:
                derived["диапазон_завершения"] = {
                    "от": str(min(completed_dates).date()),
                    "до": str(max(completed_dates).date()),
                }

    return derived
