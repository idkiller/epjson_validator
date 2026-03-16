"""Validation pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from epjson_validator.config import STAGE_ORDER
from epjson_validator.diagnostics import IssueCollector, ValidationReport, build_summary
from epjson_validator.geometry import build_geometry_rules, extract_geometry, validate_geometry
from epjson_validator.loader import detect_version, load_epjson
from epjson_validator.parametric import expand_parametric_data
from epjson_validator.reference import build_reference_index, validate_references
from epjson_validator.schema import detect_schema_version, load_raw_schema, validate_against_raw_schema


def validate_file(
    path: str | Path,
    *,
    schema_path: str | Path,
    stage: str = "geometry",
    expand_parametric: bool = False,
    parametric_run: int | None = None,
) -> ValidationReport:
    loaded = load_epjson(path)
    return validate_data(
        loaded.data,
        schema_path=schema_path,
        stage=stage,
        expand_parametric=expand_parametric,
        parametric_run=parametric_run,
    )


def validate_data(
    data: dict[str, Any],
    *,
    schema_path: str | Path | None = None,
    raw_schema: dict[str, Any] | None = None,
    stage: str = "geometry",
    expand_parametric: bool = False,
    parametric_run: int | None = None,
) -> ValidationReport:
    if raw_schema is None:
        if schema_path is None:
            raise ValueError("Either 'schema_path' or 'raw_schema' must be provided.")
        raw_schema = load_raw_schema(schema_path)

    parametric_result = None
    if expand_parametric:
        parametric_result = expand_parametric_data(data, run_index=parametric_run)
        data = parametric_result.data

    collector = IssueCollector()
    detected_ep_version = detect_version(data)
    schema_version = detect_schema_version(raw_schema)

    if _should_run(stage, "schema"):
        validate_against_raw_schema(data, raw_schema, collector, detected_ep_version)

    reference_index = build_reference_index(raw_schema)
    if _should_run(stage, "reference"):
        validate_references(data, reference_index, collector, detected_ep_version)

    geometry_rules = build_geometry_rules(raw_schema)
    geometry_model = extract_geometry(data, geometry_rules)
    if _should_run(stage, "geometry"):
        validate_geometry(geometry_model, geometry_rules, collector, detected_ep_version)

    summary = build_summary(collector.issues)
    ok = summary["error_count"] == 0 and summary["unsupported_count"] == 0
    return ValidationReport(
        ok=ok,
        issues=collector.issues,
        summary=summary,
        ep_version=detected_ep_version,
        schema_version=schema_version,
        parametric_expanded=bool(parametric_result and parametric_result.expanded),
        parametric_run=parametric_result.run_index if parametric_result else None,
        parametric_available_runs=parametric_result.available_runs if parametric_result else 0,
    )


def _should_run(selected_stage: str, current_stage: str) -> bool:
    return STAGE_ORDER[current_stage] <= STAGE_ORDER[selected_stage]
