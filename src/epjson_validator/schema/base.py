"""Schema validation primitives."""

from __future__ import annotations

import math
from typing import Any

from epjson_validator.diagnostics import IssueCollector
from epjson_validator.models import FieldSchema, ObjectSchema, VersionSchema


_SIMPLE_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
    "vertices": (list,),
}


def validate_against_schema(
    data: dict[str, Any],
    schema: VersionSchema | None,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if not isinstance(data, dict):
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            "epJSON document must be a JSON object.",
            ep_version=ep_version,
        )
        return
    if schema is None:
        return
    for category, raw_objects in data.items():
        if category in {"epjson_version", "schema_version"}:
            continue
        object_schema = schema.get_object(category)
        if object_schema is None:
            collector.add(
                "UNSUPPORTED",
                "schema",
                "unsupported",
                f"Category '{category}' is not supported by schema {schema.ep_version}.",
                path=category,
                category=category,
                ep_version=ep_version,
            )
            continue
        _validate_category(category, raw_objects, object_schema, collector, ep_version)


def _validate_category(
    category: str,
    raw_objects: Any,
    object_schema: ObjectSchema,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if category == "Version":
        if not isinstance(raw_objects, dict):
            collector.add(
                "SCHEMA_ERROR",
                "schema",
                "error",
                f"Category '{category}' must be an object.",
                path=category,
                category=category,
                ep_version=ep_version,
            )
            return
        if "Version 1" in raw_objects and isinstance(raw_objects["Version 1"], dict):
            _validate_object(category, "Version 1", raw_objects["Version 1"], object_schema, collector, ep_version)
        else:
            _validate_object(category, "Version 1", raw_objects, object_schema, collector, ep_version)
        return
    if not isinstance(raw_objects, dict):
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Category '{category}' must map object names to objects.",
            path=category,
            category=category,
            ep_version=ep_version,
        )
        return
    for object_name, obj in raw_objects.items():
        if not isinstance(obj, dict):
            collector.add(
                "SCHEMA_ERROR",
                "schema",
                "error",
                f"Object '{object_name}' in '{category}' must be a JSON object.",
                path=f"{category}.{object_name}",
                category=category,
                object_name=object_name,
                ep_version=ep_version,
            )
            continue
        _validate_object(category, object_name, obj, object_schema, collector, ep_version)


def _validate_object(
    category: str,
    object_name: str,
    obj: dict[str, Any],
    object_schema: ObjectSchema,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    for field_name, field_schema in object_schema.fields.items():
        if field_schema.required and field_name not in obj:
            collector.add(
                "SCHEMA_ERROR",
                "schema",
                "error",
                f"Missing required field '{field_name}'.",
                path=f"{category}.{object_name}.{field_name}",
                category=category,
                object_name=object_name,
                suggestion=f"Add '{field_name}' to '{object_name}'.",
                ep_version=ep_version,
            )
    if not object_schema.allow_additional_fields:
        for field_name in obj:
            if field_name not in object_schema.fields:
                collector.add(
                    "SCHEMA_WARNING",
                    "schema",
                    "warning",
                    f"Field '{field_name}' is not defined in schema for '{category}'.",
                    path=f"{category}.{object_name}.{field_name}",
                    category=category,
                    object_name=object_name,
                    ep_version=ep_version,
                )
    for field_name, value in obj.items():
        field_schema = object_schema.fields.get(field_name)
        if field_schema is None:
            continue
        _validate_field(category, object_name, field_schema, value, collector, ep_version)


def _validate_field(
    category: str,
    object_name: str,
    field_schema: FieldSchema,
    value: Any,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    expected_types = _SIMPLE_TYPES.get(field_schema.field_type, ())
    if expected_types and not isinstance(value, expected_types):
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Field '{field_schema.name}' must be of type '{field_schema.field_type}'.",
            path=f"{category}.{object_name}.{field_schema.name}",
            category=category,
            object_name=object_name,
            details={"actual_type": type(value).__name__},
            ep_version=ep_version,
        )
        return
    if field_schema.field_type == "number" and isinstance(value, bool):
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Field '{field_schema.name}' must be numeric.",
            path=f"{category}.{object_name}.{field_schema.name}",
            category=category,
            object_name=object_name,
            ep_version=ep_version,
        )
        return
    if field_schema.field_type == "number" and isinstance(value, (int, float)) and not math.isfinite(float(value)):
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Field '{field_schema.name}' must be finite.",
            path=f"{category}.{object_name}.{field_schema.name}",
            category=category,
            object_name=object_name,
            ep_version=ep_version,
        )
    if field_schema.enum_values and isinstance(value, str) and value not in field_schema.enum_values:
        collector.add(
            "SCHEMA_ERROR",
            "schema",
            "error",
            f"Field '{field_schema.name}' has unsupported value '{value}'.",
            path=f"{category}.{object_name}.{field_schema.name}",
            category=category,
            object_name=object_name,
            details={"allowed": field_schema.enum_values},
            ep_version=ep_version,
        )
    if field_schema.field_type in {"array", "vertices"} and isinstance(value, list) and field_schema.item_type:
        for index, item in enumerate(value):
            if not _item_matches(field_schema.item_type, item):
                collector.add(
                    "SCHEMA_ERROR",
                    "schema",
                    "error",
                    f"Array item {index} in '{field_schema.name}' must be '{field_schema.item_type}'.",
                    path=f"{category}.{object_name}.{field_schema.name}[{index}]",
                    category=category,
                    object_name=object_name,
                    ep_version=ep_version,
                )


def _item_matches(item_type: str, item: Any) -> bool:
    if item_type == "string":
        return isinstance(item, str)
    if item_type == "number":
        return isinstance(item, (int, float)) and not isinstance(item, bool)
    if item_type == "object":
        return isinstance(item, dict)
    return True
