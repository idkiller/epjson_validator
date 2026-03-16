"""Geometry rule models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GeometryCategoryRule:
    category: str
    vertices_field: str
    parent_fields: tuple[str, ...] = ()
    containment_parent_field: str | None = None
    zone_field: str | None = None
    surface_type_field: str | None = None


@dataclass(slots=True)
class GeometryRules:
    categories: dict[str, GeometryCategoryRule] = field(default_factory=dict)
