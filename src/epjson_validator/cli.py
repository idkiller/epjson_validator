"""Typer CLI entry point."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import typer

from epjson_validator.config import DEFAULT_PROFILE, DEFAULT_STAGE, VALID_PROFILES, VALID_STAGES
from epjson_validator.loader import inspect_data, load_epjson
from epjson_validator.pipeline.validate import validate_file
from epjson_validator.schema.converter import convert_raw_schema, load_raw_schema, version_schema_to_dict

app = typer.Typer(help="Validate EnergyPlus epJSON files.")


def _render_human_report(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"EnergyPlus version: {report['ep_version'] or 'unknown'}")
    lines.append(f"Schema version: {report['schema_version'] or 'unknown'}")
    lines.append(f"OK: {'yes' if report['ok'] else 'no'}")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for issue in report["issues"]:
        grouped[issue["stage"]].append(issue)
    for stage in ("schema", "reference", "geometry", "visualization"):
        issues = grouped.get(stage)
        if not issues:
            continue
        lines.append("")
        lines.append(stage.upper())
        for issue in issues:
            location_bits = [bit for bit in (issue.get("category"), issue.get("object_name"), issue.get("path")) if bit]
            location = " | ".join(location_bits)
            suffix = f" [{location}]" if location else ""
            lines.append(f"- {issue['severity'].upper()} {issue['code']}: {issue['message']}{suffix}")
    lines.append("")
    summary = report["summary"]
    lines.append("Summary")
    lines.append(f"- errors: {summary['error_count']}")
    lines.append(f"- warnings: {summary['warning_count']}")
    lines.append(f"- info: {summary['info_count']}")
    lines.append(f"- unsupported: {summary['unsupported_count']}")
    lines.append(f"- counts_by_stage: {json.dumps(summary['counts_by_stage'], sort_keys=True)}")
    return "\n".join(lines)


def _exit_code(report: dict, fail_on_warning: bool) -> int:
    summary = report["summary"]
    if summary["error_count"] > 0:
        return 1
    if fail_on_warning and summary["warning_count"] > 0:
        return 1
    return 0


@app.command()
def validate(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to epJSON file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON report."),
    stage: str = typer.Option(DEFAULT_STAGE, "--stage", help="Validation stage cutoff."),
    profile: str = typer.Option(DEFAULT_PROFILE, "--profile", help="Visualization profile."),
    fail_on_warning: bool = typer.Option(False, "--fail-on-warning", help="Fail when warnings exist."),
    ep_version: str | None = typer.Option(None, "--ep-version", help="Override EnergyPlus version."),
) -> None:
    if stage not in VALID_STAGES:
        raise typer.BadParameter(f"Unsupported stage '{stage}'. Expected one of {', '.join(VALID_STAGES)}.")
    if profile not in VALID_PROFILES:
        raise typer.BadParameter(f"Unsupported profile '{profile}'. Expected one of {', '.join(VALID_PROFILES)}.")
    report = validate_file(path, ep_version=ep_version, stage=stage, profile=profile).to_dict()
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo(_render_human_report(report))
    raise typer.Exit(code=_exit_code(report, fail_on_warning))


@app.command()
def inspect(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to epJSON file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    ep_version: str | None = typer.Option(None, "--ep-version", help="Override EnergyPlus version."),
) -> None:
    loaded = load_epjson(path)
    info = inspect_data(loaded.data, ep_version)
    payload = {
        "ep_version": info.ep_version,
        "object_count": info.object_count,
        "categories": info.categories,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    typer.echo(f"EnergyPlus version: {payload['ep_version'] or 'unknown'}")
    typer.echo(f"Object count: {payload['object_count']}")
    for category, count in sorted(payload["categories"].items()):
        typer.echo(f"- {category}: {count}")


@app.command()
def stats(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to epJSON file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    ep_version: str | None = typer.Option(None, "--ep-version", help="Override EnergyPlus version."),
) -> None:
    loaded = load_epjson(path)
    info = inspect_data(loaded.data, ep_version)
    payload = {
        "ep_version": info.ep_version,
        "category_count": len(info.categories),
        "object_count": info.object_count,
        "categories": info.categories,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    typer.echo(f"EnergyPlus version: {payload['ep_version'] or 'unknown'}")
    typer.echo(f"Categories: {payload['category_count']}")
    typer.echo(f"Objects: {payload['object_count']}")


@app.command("convert-schema")
def convert_schema(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to Energy+.schema.epJSON file."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Optional output path for converted JSON."),
    ep_version: str = typer.Option("24.2.0", "--ep-version", help="Version label to assign to converted schema."),
) -> None:
    raw_schema = load_raw_schema(path)
    converted = convert_raw_schema(raw_schema, ep_version=ep_version)
    payload = version_schema_to_dict(converted)

    if output is None:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    typer.echo(f"Converted schema written to: {output}")
