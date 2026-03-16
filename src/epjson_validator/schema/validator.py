"""Schema validation against raw EnergyPlus epJSON schemas."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

from epjson_validator.diagnostics import IssueCollector


def validate_against_raw_schema(
    data: dict[str, Any],
    raw_schema: dict[str, Any],
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    try:
        validator = Draft7Validator(raw_schema)
    except SchemaError as exc:
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Raw schema is not a valid Draft 7 schema: {exc.message}",
            ep_version=ep_version,
        )
        return

    errors = sorted(validator.iter_errors(data), key=_error_sort_key)
    for error in errors:
        path = _format_error_path(error.absolute_path)
        if error.validator == "required":
            missing = _extract_required_field(error.message)
            if missing:
                path = f"{path}.{missing}" if path else missing
        category, object_name = _extract_context(path)
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            error.message,
            path=path or None,
            category=category,
            object_name=object_name,
            ep_version=ep_version,
        )


def _error_sort_key(error: Any) -> tuple[str, str]:
    return (_format_error_path(error.absolute_path), error.message)


def _format_error_path(path_parts: Iterable[Any]) -> str:
    parts: list[str] = []
    for part in path_parts:
        if isinstance(part, int):
            if not parts:
                parts.append(f"[{part}]")
            else:
                parts[-1] = f"{parts[-1]}[{part}]"
            continue
        part_str = str(part)
        parts.append(part_str)
    return ".".join(parts)


def _extract_context(path: str) -> tuple[str | None, str | None]:
    if not path:
        return (None, None)
    parts = path.split(".")
    category = parts[0] if parts else None
    object_name = parts[1] if len(parts) > 1 else None
    return (category, object_name)


def _extract_required_field(message: str) -> str | None:
    if "required property" not in message:
        return None
    bits = message.split("'")
    if len(bits) < 2:
        return None
    return bits[1]
