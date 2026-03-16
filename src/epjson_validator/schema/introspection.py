"""Helpers for walking raw EnergyPlus epJSON schemas."""

from __future__ import annotations

from typing import Any


def extract_object_entries(raw_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    properties = raw_schema.get("properties")
    if not isinstance(properties, dict):
        return {}

    entries: dict[str, dict[str, Any]] = {}
    for key, value in properties.items():
        if key in {"epjson_version", "schema_version"}:
            continue
        if isinstance(value, dict):
            entries[key] = value
    return entries


def resolve_object_instance_schema(category_schema: dict[str, Any]) -> dict[str, Any] | None:
    pattern_props = category_schema.get("patternProperties")
    if isinstance(pattern_props, dict):
        for pattern_schema in pattern_props.values():
            if isinstance(pattern_schema, dict) and isinstance(pattern_schema.get("properties"), dict):
                return pattern_schema

    additional = category_schema.get("additionalProperties")
    if isinstance(additional, dict) and isinstance(additional.get("properties"), dict):
        return additional

    if isinstance(category_schema.get("properties"), dict):
        return category_schema

    return None


def extract_field_schemas(category_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    instance_schema = resolve_object_instance_schema(category_schema)
    if not instance_schema:
        return {}
    raw_fields = instance_schema.get("properties")
    if not isinstance(raw_fields, dict):
        return {}
    return {
        field_name: field_schema
        for field_name, field_schema in raw_fields.items()
        if isinstance(field_schema, dict)
    }


def extract_required_fields(category_schema: dict[str, Any]) -> set[str]:
    instance_schema = resolve_object_instance_schema(category_schema)
    if not instance_schema:
        return set()
    return set(as_str_list(instance_schema.get("required")))


def extract_name_namespaces(category_schema: dict[str, Any]) -> tuple[str, ...]:
    name_schema = category_schema.get("name")
    if not isinstance(name_schema, dict):
        return ()
    return tuple(as_str_list(name_schema.get("reference")))


def as_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
