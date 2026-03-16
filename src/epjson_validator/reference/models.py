"""Reference validation models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReferenceFieldRule:
    field_name: str
    target_namespaces: tuple[str, ...]
    is_array: bool = False


@dataclass(slots=True)
class ReferenceIndex:
    namespaces_by_category: dict[str, tuple[str, ...]] = field(default_factory=dict)
    fields_by_category: dict[str, dict[str, ReferenceFieldRule]] = field(default_factory=dict)
