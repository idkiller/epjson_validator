"""Shared lightweight models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
