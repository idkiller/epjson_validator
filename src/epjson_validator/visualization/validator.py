"""Visualization validation."""

from __future__ import annotations

import math

from epjson_validator.config import ZERO_AREA_TOLERANCE
from epjson_validator.diagnostics import IssueCollector
from epjson_validator.geometry.math_utils import centroid, polygon_self_intersects, signed_area_2d
from epjson_validator.geometry.models import GeometryModel
from epjson_validator.models import VersionSchema
from epjson_validator.visualization.profiles import MVP_RENDER_PROFILES


def validate_visualization(
    model: GeometryModel,
    schema: VersionSchema | None,
    profile: str,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if profile not in MVP_RENDER_PROFILES:
        collector.add(
            "UNSUPPORTED",
            "visualization",
            "unsupported",
            f"Visualization profile '{profile}' is not implemented in this MVP.",
            details={"profile": profile},
            ep_version=ep_version,
        )
        return
    schema_objects = schema.objects if schema else {}
    for polygon in model.polygons:
        object_schema = schema_objects.get(polygon.category)
        if object_schema and not object_schema.visualization_supported:
            collector.add(
                "UNSUPPORTED",
                "visualization",
                "unsupported",
                f"Category '{polygon.category}' is not supported by visualization profile '{profile}'.",
                path=f"{polygon.category}.{polygon.object_name}",
                category=polygon.category,
                object_name=polygon.object_name,
                ep_version=ep_version,
            )
            continue
        projected = [(vertex.x, vertex.y) for vertex in polygon.vertices]
        projected_area = abs(signed_area_2d(projected)) if len(projected) >= 3 else 0.0
        if projected_area <= ZERO_AREA_TOLERANCE:
            collector.add(
                "VIS_WARNING",
                "visualization",
                "warning",
                "Polygon has unstable XY projection for svg-plan output.",
                path=f"{polygon.category}.{polygon.object_name}.vertices",
                category=polygon.category,
                object_name=polygon.object_name,
                ep_version=ep_version,
            )
        if len(projected) >= 4 and polygon_self_intersects(projected):
            collector.add(
                "VIS_WARNING",
                "visualization",
                "warning",
                "Polygon may not triangulate cleanly in svg-plan projection.",
                path=f"{polygon.category}.{polygon.object_name}.vertices",
                category=polygon.category,
                object_name=polygon.object_name,
                ep_version=ep_version,
            )
        c = centroid(polygon.vertices)
        if not all(math.isfinite(component) for component in (c.x, c.y, c.z)):
            collector.add(
                "VIS_ERROR",
                "visualization",
                "error",
                "Polygon centroid could not be computed.",
                path=f"{polygon.category}.{polygon.object_name}.vertices",
                category=polygon.category,
                object_name=polygon.object_name,
                ep_version=ep_version,
            )
        elif polygon.surface_type == "Floor":
            collector.add(
                "VIS_INFO",
                "visualization",
                "info",
                "Floor surface can contribute to footprint extraction in svg-plan.",
                path=f"{polygon.category}.{polygon.object_name}",
                category=polygon.category,
                object_name=polygon.object_name,
                ep_version=ep_version,
            )
