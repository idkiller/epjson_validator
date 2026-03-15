"""epJSON loading and version detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from epjson_validator.models import InspectInfo, LoadedEPJSON


def load_epjson(path: str | Path) -> LoadedEPJSON:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return LoadedEPJSON(
        data=data,
        source=str(file_path),
        detected_version=detect_version(data),
    )


def detect_version(data: dict[str, Any]) -> str | None:
    version_obj = data.get("Version")
    if isinstance(version_obj, dict):
        version_identifier = version_obj.get("Version 1")
        if isinstance(version_identifier, dict):
            candidate = version_identifier.get("version_identifier")
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        candidate = version_obj.get("version_identifier")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    candidate = data.get("epjson_version") or data.get("schema_version")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return None


def resolve_version(data: dict[str, Any], override: str | None) -> str | None:
    return override or detect_version(data)


def inspect_data(data: dict[str, Any], override: str | None = None) -> InspectInfo:
    categories: dict[str, int] = {}
    object_count = 0
    for category, raw_objects in data.items():
        if category in {"epjson_version", "schema_version"}:
            continue
        if isinstance(raw_objects, dict):
            count = 1 if category == "Version" and raw_objects else len(raw_objects)
            categories[category] = count
            object_count += count
    return InspectInfo(ep_version=resolve_version(data, override), categories=categories, object_count=object_count)
