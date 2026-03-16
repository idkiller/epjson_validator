"""Load EnergyPlus raw epJSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from epjson_validator.schema.introspection import resolve_object_instance_schema


def load_raw_schema(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_schema_version(raw_schema: dict[str, Any]) -> str | None:
    properties = raw_schema.get("properties")
    if not isinstance(properties, dict):
        return None
    version_schema = properties.get("Version")
    if not isinstance(version_schema, dict):
        return None
    instance_schema = resolve_object_instance_schema(version_schema)
    if not instance_schema:
        return None
    fields = instance_schema.get("properties")
    if not isinstance(fields, dict):
        return None
    version_identifier = fields.get("version_identifier")
    if not isinstance(version_identifier, dict):
        return None
    default = version_identifier.get("default")
    if isinstance(default, str) and default.strip():
        return default.strip()
    if isinstance(default, (int, float)):
        return str(default)
    return None
