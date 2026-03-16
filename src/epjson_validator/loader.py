"""epJSON loading and version detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from epjson_validator.models import InspectInfo, LoadedEPJSON


class EPJSONLoadError(ValueError):
    """Raised when an input file cannot be loaded as epJSON."""


def load_epjson(path: str | Path) -> LoadedEPJSON:
    file_path = Path(path)
    if file_path.suffix.lower() == ".idf":
        raise EPJSONLoadError(
            f"'{file_path.name}' looks like an IDF file. This tool validates epJSON, not IDF."
        )
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise EPJSONLoadError(
            f"Failed to parse '{file_path.name}' as epJSON JSON. Provide an epJSON file, not IDF or other text."
        ) from exc
    if not isinstance(data, dict):
        raise EPJSONLoadError("epJSON document must be a JSON object.")
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


def inspect_data(data: dict[str, Any]) -> InspectInfo:
    categories: dict[str, int] = {}
    object_count = 0
    for category, raw_objects in data.items():
        if category in {"epjson_version", "schema_version"}:
            continue
        if isinstance(raw_objects, dict):
            count = 1 if category == "Version" and raw_objects else len(raw_objects)
            categories[category] = count
            object_count += count
    return InspectInfo(ep_version=detect_version(data), categories=categories, object_count=object_count)
