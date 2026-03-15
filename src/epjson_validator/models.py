"""Internal schema models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FieldSchema:
    name: str
    field_type: str
    required: bool = False
    enum_values: list[str] | None = None
    reference_target: str | None = None
    semantic_type: str | None = None
    item_type: str | None = None


@dataclass(slots=True)
class ObjectSchema:
    name: str
    fields: dict[str, FieldSchema]
    geometry_supported: bool = False
    visualization_supported: bool = False
    allow_additional_fields: bool = True


@dataclass(slots=True)
class VersionSchema:
    ep_version: str
    objects: dict[str, ObjectSchema]

    def get_object(self, category: str) -> ObjectSchema | None:
        return self.objects.get(category)


@dataclass(slots=True)
class LoadedEPJSON:
    data: dict[str, Any]
    source: str | None = None
    detected_version: str | None = None


@dataclass(slots=True)
class InspectInfo:
    ep_version: str | None
    categories: dict[str, int] = field(default_factory=dict)
    object_count: int = 0
