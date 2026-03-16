"""Geometry validation."""

from __future__ import annotations

from epjson_validator.config import DISTINCT_TOLERANCE, PLANAR_TOLERANCE, ZERO_AREA_TOLERANCE
from epjson_validator.diagnostics import IssueCollector
from epjson_validator.geometry.math_utils import (
    are_finite,
    dominant_axis,
    max_distance_to_plane,
    plane_normal,
    point_in_polygon,
    polygon_area,
    polygon_self_intersects,
    project_to_2d,
    signed_area_2d,
)
from epjson_validator.geometry.models import GeometryModel, Polygon3D
from epjson_validator.geometry.rules import GeometryRules


def validate_geometry(
    model: GeometryModel,
    rules: GeometryRules,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    polygon_index = {_normalize_name(polygon.object_name): polygon for polygon in model.polygons}
    for polygon in model.polygons:
        _validate_polygon(polygon, collector, ep_version)
        category_rule = rules.categories.get(polygon.category)
        if category_rule and category_rule.containment_parent_field:
            _validate_parent_containment(polygon, polygon_index, collector, ep_version)


def _validate_polygon(polygon: Polygon3D, collector: IssueCollector, ep_version: str | None) -> None:
    if len(polygon.vertices) < 3:
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Polygon must have at least 3 vertices.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
        return
    if not are_finite(polygon.vertices):
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Polygon vertices must have finite coordinates.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
        return
    distinct = {(round(vertex.x, 7), round(vertex.y, 7), round(vertex.z, 7)) for vertex in polygon.vertices}
    if len(distinct) < 3:
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Polygon vertices must contain at least 3 distinct points.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
        return
    if len(distinct) != len(polygon.vertices):
        collector.add(
            "GEOMETRY_WARNING",
            "geometry",
            "warning",
            "Polygon contains duplicate vertices.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
    area = polygon_area(polygon.vertices)
    if area <= ZERO_AREA_TOLERANCE:
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Polygon area is zero or too small.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
    distance = max_distance_to_plane(polygon.vertices)
    if distance > PLANAR_TOLERANCE:
        collector.add(
            "GEOMETRY_WARNING",
            "geometry",
            "warning",
            "Polygon is not approximately planar.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            details={"max_distance": distance},
            ep_version=ep_version,
        )
    normal = plane_normal(polygon.vertices)
    axis = dominant_axis(normal)
    projected = [project_to_2d(vertex, axis) for vertex in polygon.vertices]
    if polygon_self_intersects(projected):
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Polygon self-intersects in projected plane.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )
    if abs(signed_area_2d(projected)) <= DISTINCT_TOLERANCE:
        collector.add(
            "GEOMETRY_WARNING",
            "geometry",
            "warning",
            "Polygon winding is unstable after projection.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            ep_version=ep_version,
        )


def _validate_parent_containment(
    polygon: Polygon3D,
    polygon_index: dict[str, Polygon3D],
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if not polygon.parent_name:
        return
    parent = polygon_index.get(_normalize_name(polygon.parent_name))
    if parent is None or len(parent.vertices) < 3 or len(polygon.vertices) < 3:
        return
    parent_normal = plane_normal(parent.vertices)
    axis = dominant_axis(parent_normal)
    origin = parent.vertices[0]
    max_distance = 0.0
    for vertex in polygon.vertices:
        distance = abs(
            (vertex.x - origin.x) * parent_normal.x
            + (vertex.y - origin.y) * parent_normal.y
            + (vertex.z - origin.z) * parent_normal.z
        )
        max_distance = max(max_distance, distance)
    if max_distance > PLANAR_TOLERANCE:
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Child polygon vertices are not coplanar with the parent surface.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            details={"parent_surface": polygon.parent_name, "max_distance": max_distance},
            ep_version=ep_version,
        )
    parent_points = [project_to_2d(vertex, axis) for vertex in parent.vertices]
    child_points = [project_to_2d(vertex, axis) for vertex in polygon.vertices]
    if any(not point_in_polygon(point, parent_points) for point in child_points):
        collector.add(
            "GEOMETRY_ERROR",
            "geometry",
            "error",
            "Child polygon is not contained within the parent surface boundary.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            details={"parent_surface": polygon.parent_name},
            ep_version=ep_version,
        )
    if signed_area_2d(parent_points) * signed_area_2d(child_points) < 0:
        collector.add(
            "GEOMETRY_WARNING",
            "geometry",
            "warning",
            "Child polygon winding differs from parent surface winding.",
            path=f"{polygon.category}.{polygon.object_name}.vertices",
            category=polygon.category,
            object_name=polygon.object_name,
            details={"parent_surface": polygon.parent_name},
            ep_version=ep_version,
        )


def _normalize_name(value: str) -> str:
    return value.strip().casefold()
