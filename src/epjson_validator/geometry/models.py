"""Geometry data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Vec3:
    x: float
    y: float
    z: float


@dataclass(slots=True)
class Polygon3D:
    id: str
    category: str
    object_name: str
    vertices: list[Vec3]
    parent_name: str | None = None
    zone_name: str | None = None
    surface_type: str | None = None


@dataclass(slots=True)
class GeometryModel:
    polygons: list[Polygon3D]
    bounds: dict[str, float] | None = None
