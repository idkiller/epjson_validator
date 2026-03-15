"""Geometry math helpers."""

from __future__ import annotations

import math

from epjson_validator.geometry.models import Vec3


def subtract(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(a.x - b.x, a.y - b.y, a.z - b.z)


def dot(a: Vec3, b: Vec3) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def cross(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def length(v: Vec3) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: Vec3) -> Vec3:
    magnitude = length(v)
    if magnitude == 0:
        return Vec3(0.0, 0.0, 0.0)
    return Vec3(v.x / magnitude, v.y / magnitude, v.z / magnitude)


def centroid(vertices: list[Vec3]) -> Vec3:
    count = len(vertices)
    if count == 0:
        return Vec3(0.0, 0.0, 0.0)
    return Vec3(
        sum(v.x for v in vertices) / count,
        sum(v.y for v in vertices) / count,
        sum(v.z for v in vertices) / count,
    )


def plane_normal(vertices: list[Vec3]) -> Vec3:
    nx = ny = nz = 0.0
    count = len(vertices)
    for index, current in enumerate(vertices):
        nxt = vertices[(index + 1) % count]
        nx += (current.y - nxt.y) * (current.z + nxt.z)
        ny += (current.z - nxt.z) * (current.x + nxt.x)
        nz += (current.x - nxt.x) * (current.y + nxt.y)
    return normalize(Vec3(nx, ny, nz))


def polygon_area(vertices: list[Vec3]) -> float:
    normal = plane_normal(vertices)
    axis = dominant_axis(normal)
    projected = [project_to_2d(vertex, axis) for vertex in vertices]
    return abs(signed_area_2d(projected))


def max_distance_to_plane(vertices: list[Vec3]) -> float:
    if len(vertices) < 3:
        return 0.0
    origin = vertices[0]
    normal = plane_normal(vertices)
    return max(abs(dot(subtract(vertex, origin), normal)) for vertex in vertices)


def dominant_axis(normal: Vec3) -> int:
    components = [abs(normal.x), abs(normal.y), abs(normal.z)]
    return max(range(3), key=components.__getitem__)


def project_to_2d(vertex: Vec3, axis: int) -> tuple[float, float]:
    if axis == 0:
        return (vertex.y, vertex.z)
    if axis == 1:
        return (vertex.x, vertex.z)
    return (vertex.x, vertex.y)


def signed_area_2d(points: list[tuple[float, float]]) -> float:
    area = 0.0
    for index, current in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        area += current[0] * nxt[1] - nxt[0] * current[1]
    return area / 2.0


def polygon_self_intersects(points: list[tuple[float, float]]) -> bool:
    count = len(points)
    if count < 4:
        return False
    for i in range(count):
        a1 = points[i]
        a2 = points[(i + 1) % count]
        for j in range(i + 1, count):
            if abs(i - j) <= 1 or {i, j} == {0, count - 1}:
                continue
            b1 = points[j]
            b2 = points[(j + 1) % count]
            if segments_intersect(a1, a2, b1, b2):
                return True
    return False


def segments_intersect(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    def orientation(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> bool:
        return (
            min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
        )

    o1 = orientation(a1, a2, b1)
    o2 = orientation(a1, a2, b2)
    o3 = orientation(b1, b2, a1)
    o4 = orientation(b1, b2, a2)

    if (o1 > 0 > o2 or o1 < 0 < o2) and (o3 > 0 > o4 or o3 < 0 < o4):
        return True
    if o1 == 0 and on_segment(a1, b1, a2):
        return True
    if o2 == 0 and on_segment(a1, b2, a2):
        return True
    if o3 == 0 and on_segment(b1, a1, b2):
        return True
    if o4 == 0 and on_segment(b1, a2, b2):
        return True
    return False


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    inside = False
    px, py = point
    for index, current in enumerate(polygon):
        nxt = polygon[(index + 1) % len(polygon)]
        x1, y1 = current
        x2, y2 = nxt
        intersects = ((y1 > py) != (y2 > py)) and (
            px < (x2 - x1) * (py - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if intersects:
            inside = not inside
    return inside


def are_finite(vertices: list[Vec3]) -> bool:
    return all(math.isfinite(component) for vertex in vertices for component in (vertex.x, vertex.y, vertex.z))
