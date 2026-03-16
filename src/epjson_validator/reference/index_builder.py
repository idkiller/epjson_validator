"""Build namespace-oriented reference indexes from raw schemas."""

from __future__ import annotations

from typing import Any

from epjson_validator.reference.models import ReferenceFieldRule, ReferenceIndex
from epjson_validator.schema.introspection import as_str_list, extract_field_schemas, extract_name_namespaces, extract_object_entries


def build_reference_index(raw_schema: dict[str, Any]) -> ReferenceIndex:
    index = ReferenceIndex()
    for category_name, category_schema in extract_object_entries(raw_schema).items():
        index.namespaces_by_category[category_name] = extract_name_namespaces(category_schema)
        field_rules: dict[str, ReferenceFieldRule] = {}
        for field_name, field_schema in extract_field_schemas(category_schema).items():
            target_namespaces = _extract_target_namespaces(field_schema)
            if not target_namespaces:
                continue
            field_rules[field_name] = ReferenceFieldRule(
                field_name=field_name,
                target_namespaces=target_namespaces,
                is_array=_is_array_reference(field_schema),
            )
        index.fields_by_category[category_name] = field_rules
    return index


def _extract_target_namespaces(raw_field: dict[str, Any]) -> tuple[str, ...]:
    namespaces: list[str] = []
    namespaces.extend(as_str_list(raw_field.get("object_list")))
    namespaces.extend(as_str_list(raw_field.get("reference")))

    items = raw_field.get("items")
    if isinstance(items, dict):
        namespaces.extend(as_str_list(items.get("object_list")))
        namespaces.extend(as_str_list(items.get("reference")))

    filtered = [namespace for namespace in dict.fromkeys(namespaces) if not _is_type_namespace(namespace)]
    return tuple(filtered)


def _is_array_reference(raw_field: dict[str, Any]) -> bool:
    raw_type = raw_field.get("type")
    if raw_type == "array":
        return True
    return isinstance(raw_field.get("items"), dict)


def _is_type_namespace(namespace: str) -> bool:
    return namespace.endswith("Types")
