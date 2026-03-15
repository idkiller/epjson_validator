"""Validation pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from epjson_validator.config import STAGE_ORDER
from epjson_validator.diagnostics import IssueCollector, ValidationReport, build_summary
from epjson_validator.geometry.normalize import normalize_geometry
from epjson_validator.geometry.validator import validate_geometry
from epjson_validator.loader import load_epjson, resolve_version
from epjson_validator.reference.validator import validate_references
from epjson_validator.registry import build_registry
from epjson_validator.schema.base import validate_against_schema
from epjson_validator.schema.loader import load_version_schema
from epjson_validator.visualization.validator import validate_visualization


def validate_file(
    path: str | Path,
    *,
    ep_version: str | None = None,
    stage: str = "visualization",
    profile: str = "svg-plan",
) -> ValidationReport:
    loaded = load_epjson(path)
    return validate_data(loaded.data, ep_version=ep_version, stage=stage, profile=profile)


def validate_data(
    data: dict[str, Any],
    *,
    ep_version: str | None = None,
    stage: str = "visualization",
    profile: str = "svg-plan",
) -> ValidationReport:
    collector = IssueCollector()
    resolved_version = resolve_version(data, ep_version)
    schema = load_version_schema(resolved_version)
    if resolved_version is None:
        collector.add(
            "UNSUPPORTED",
            "schema",
            "unsupported",
            "Could not detect EnergyPlus version and no override was provided.",
            suggestion="Add a Version object or pass --ep-version.",
            ep_version=resolved_version,
        )
    elif schema is None:
        collector.add(
            "UNSUPPORTED",
            "schema",
            "unsupported",
            f"EnergyPlus version '{resolved_version}' is not supported.",
            suggestion="Use --ep-version 24.2.0 for supported MVP validation.",
            ep_version=resolved_version,
        )
    if _should_run(stage, "schema"):
        validate_against_schema(data, schema, collector, resolved_version)
    registry = build_registry(data, schema, collector, resolved_version)
    if schema is not None and _should_run(stage, "reference"):
        validate_references(data, schema, registry, collector, resolved_version)
    geometry_model = normalize_geometry(data, schema)
    if _should_run(stage, "geometry"):
        validate_geometry(geometry_model, collector, resolved_version)
    if _should_run(stage, "visualization"):
        validate_visualization(geometry_model, schema, profile, collector, resolved_version)
    summary = build_summary(collector.issues)
    ok = summary["error_count"] == 0 and summary["unsupported_count"] == 0
    return ValidationReport(
        ok=ok,
        issues=collector.issues,
        summary=summary,
        ep_version=resolved_version,
        schema_version=schema.ep_version if schema else None,
    )


def _should_run(selected_stage: str, current_stage: str) -> bool:
    return STAGE_ORDER[current_stage] <= STAGE_ORDER[selected_stage]
