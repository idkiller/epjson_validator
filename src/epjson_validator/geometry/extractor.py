"""Extract normalized geometry from epJSON documents."""

from __future__ import annotations

import math
from typing import Any

from epjson_validator.geometry.models import GeometryModel, Polygon3D, Vec3
from epjson_validator.geometry.rules import GeometryRules


def extract_geometry(data: dict[str, Any], rules: GeometryRules) -> GeometryModel:
    polygons: list[Polygon3D] = []
    for category, category_rule in rules.categories.items():
        raw_objects = data.get(category)
        if not isinstance(raw_objects, dict):
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            vertices = [
                _parse_vertex(raw_vertex)
                for raw_vertex in obj.get(category_rule.vertices_field, [])
                if isinstance(raw_vertex, dict)
            ]
            polygons.append(
                Polygon3D(
                    id=f"{category}:{object_name}",
                    category=category,
                    object_name=object_name,
                    vertices=vertices,
                    parent_name=_extract_parent_name(obj, category_rule.parent_fields),
                    zone_name=_extract_optional_str(obj, category_rule.zone_field),
                    surface_type=_extract_optional_str(obj, category_rule.surface_type_field),
                )
            )
    return GeometryModel(polygons=polygons, bounds=_compute_bounds(polygons))


def _extract_parent_name(obj: dict[str, Any], parent_fields: tuple[str, ...]) -> str | None:
    for field_name in parent_fields:
        value = obj.get(field_name)
        if isinstance(value, str) and value:
            return value
    return None


def _extract_optional_str(obj: dict[str, Any], field_name: str | None) -> str | None:
    if not field_name:
        return None
    value = obj.get(field_name)
    if isinstance(value, str) and value:
        return value
    return None


def _parse_vertex(raw_vertex: dict[str, Any]) -> Vec3:
    def number(*keys: str) -> float:
        for key in keys:
            value = raw_vertex.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return math.nan

    return Vec3(
        x=number("vertex_x_coordinate", "x"),
        y=number("vertex_y_coordinate", "y"),
        z=number("vertex_z_coordinate", "z"),
    )


def _compute_bounds(polygons: list[Polygon3D]) -> dict[str, float] | None:
    vertices = [vertex for polygon in polygons for vertex in polygon.vertices if math.isfinite(vertex.x + vertex.y + vertex.z)]
    if not vertices:
        return None
    return {
        "min_x": min(vertex.x for vertex in vertices),
        "max_x": max(vertex.x for vertex in vertices),
        "min_y": min(vertex.y for vertex in vertices),
        "max_y": max(vertex.y for vertex in vertices),
        "min_z": min(vertex.z for vertex in vertices),
        "max_z": max(vertex.z for vertex in vertices),
    }
