"""Object registry for reference validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from epjson_validator.diagnostics import IssueCollector
from epjson_validator.models import VersionSchema


@dataclass(slots=True)
class ObjectRecord:
    category: str
    name: str
    data: dict[str, Any]


@dataclass(slots=True)
class ObjectRegistry:
    categories: dict[str, dict[str, ObjectRecord]] = field(default_factory=dict)

    def add(self, category: str, name: str, data: dict[str, Any]) -> bool:
        category_bucket = self.categories.setdefault(category, {})
        if name in category_bucket:
            return False
        category_bucket[name] = ObjectRecord(category=category, name=name, data=data)
        return True

    def get(self, category: str, name: str) -> ObjectRecord | None:
        return self.categories.get(category, {}).get(name)

    def has(self, category: str, name: str) -> bool:
        return self.get(category, name) is not None


def build_registry(
    data: dict[str, Any],
    schema: VersionSchema | None,
    collector: IssueCollector,
    ep_version: str | None,
) -> ObjectRegistry:
    registry = ObjectRegistry()
    for category, raw_objects in data.items():
        if not isinstance(raw_objects, dict):
            continue
        if category == "Version":
            if raw_objects:
                registry.add(category, "Version 1", raw_objects)
            continue
        if schema and category not in schema.objects:
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            if not registry.add(category, object_name, obj):
                collector.add(
                    "REFERENCE_ERROR",
                    "reference",
                    "error",
                    f"Duplicate object name '{object_name}' in category '{category}'.",
                    path=f"{category}.{object_name}",
                    category=category,
                    object_name=object_name,
                    ep_version=ep_version,
                )
    return registry
