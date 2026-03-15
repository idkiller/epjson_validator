"""Normalize epJSON objects into geometry models."""

from __future__ import annotations

import math
from typing import Any

from epjson_validator.geometry.models import GeometryModel, Polygon3D, Vec3
from epjson_validator.models import VersionSchema


def normalize_geometry(data: dict[str, Any], schema: VersionSchema | None) -> GeometryModel:
    polygons: list[Polygon3D] = []
    supported_categories: set[str]
    if schema is None:
        supported_categories = {
            "BuildingSurface:Detailed",
            "FenestrationSurface:Detailed",
            "Shading:Zone:Detailed",
            "Shading:Building:Detailed",
            "Shading:Site:Detailed",
        }
    else:
        supported_categories = {
            name for name, object_schema in schema.objects.items() if object_schema.geometry_supported
        }
    for category in supported_categories:
        raw_objects = data.get(category)
        if not isinstance(raw_objects, dict):
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            vertices = [_parse_vertex(raw_vertex) for raw_vertex in obj.get("vertices", []) if isinstance(raw_vertex, dict)]
            polygons.append(
                Polygon3D(
                    id=f"{category}:{object_name}",
                    category=category,
                    object_name=object_name,
                    vertices=vertices,
                    parent_name=obj.get("building_surface_name") or obj.get("base_surface_name") or obj.get("outside_boundary_condition_object"),
                    zone_name=obj.get("zone_name"),
                    surface_type=obj.get("surface_type"),
                )
            )
    return GeometryModel(polygons=polygons, bounds=_compute_bounds(polygons))


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
