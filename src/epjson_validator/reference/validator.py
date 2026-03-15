"""Reference validation."""

from __future__ import annotations

from typing import Any

from epjson_validator.diagnostics import IssueCollector
from epjson_validator.models import VersionSchema
from epjson_validator.registry import ObjectRegistry


def validate_references(
    data: dict[str, Any],
    schema: VersionSchema,
    registry: ObjectRegistry,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    for category, object_schema in schema.objects.items():
        raw_objects = data.get(category)
        if category == "Version" or not isinstance(raw_objects, dict):
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            for field_name, field_schema in object_schema.fields.items():
                target = field_schema.reference_target
                if target is None or field_name not in obj:
                    continue
                value = obj[field_name]
                if field_schema.field_type == "array" and isinstance(value, list):
                    _validate_reference_array(
                        category,
                        object_name,
                        field_name,
                        target,
                        value,
                        registry,
                        collector,
                        ep_version,
                    )
                else:
                    _validate_reference_scalar(
                        category,
                        object_name,
                        field_name,
                        target,
                        value,
                        registry,
                        collector,
                        ep_version,
                    )


def _validate_reference_scalar(
    category: str,
    object_name: str,
    field_name: str,
    target: str,
    value: Any,
    registry: ObjectRegistry,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if not isinstance(value, str) or not value:
        return
    if registry.has(target, value):
        return
    collector.add(
        "REFERENCE_ERROR",
        "reference",
        "error",
        f"Reference '{field_name}' points to missing {target} '{value}'.",
        path=f"{category}.{object_name}.{field_name}",
        category=category,
        object_name=object_name,
        details={"target_category": target, "target_name": value},
        suggestion=f"Create '{value}' in '{target}' or update '{field_name}'.",
        ep_version=ep_version,
    )


def _validate_reference_array(
    category: str,
    object_name: str,
    field_name: str,
    target: str,
    values: list[Any],
    registry: ObjectRegistry,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value:
            continue
        if registry.has(target, value):
            continue
        collector.add(
            "REFERENCE_ERROR",
            "reference",
            "error",
            f"Reference list '{field_name}' contains missing {target} '{value}'.",
            path=f"{category}.{object_name}.{field_name}[{index}]",
            category=category,
            object_name=object_name,
            details={"target_category": target, "target_name": value},
            suggestion=f"Create '{value}' in '{target}' or remove it from '{field_name}'.",
            ep_version=ep_version,
        )
