"""Typer CLI entry point."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import typer

from epjson_validator.config import DEFAULT_STAGE, SCHEMA_PATH_ENVVAR, VALID_STAGES
from epjson_validator.hvac import extract_hvac_diagrams, render_diagrams_html, render_diagrams_text
from epjson_validator.loader import EPJSONLoadError, inspect_data, load_epjson
from epjson_validator.parametric import ParametricExpansionError, expand_parametric_data
from epjson_validator.pipeline.validate import validate_file

app = typer.Typer(help="Validate EnergyPlus epJSON files.")


def _render_human_report(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"EnergyPlus version: {report['ep_version'] or 'unknown'}")
    lines.append(f"Schema version: {report['schema_version'] or 'unknown'}")
    if report.get("parametric_expanded"):
        lines.append(
            f"Parametric run: {report.get('parametric_run')} / {report.get('parametric_available_runs')}"
        )
    lines.append(f"OK: {'yes' if report['ok'] else 'no'}")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for issue in report["issues"]:
        grouped[issue["stage"]].append(issue)
    for stage in ("schema", "reference", "geometry"):
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
    schema_path: Path | None = typer.Option(
        None,
        "--schema-path",
        envvar=SCHEMA_PATH_ENVVAR,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to Energy+.schema.epJSON. Falls back to EPJSON_VALIDATOR_SCHEMA_PATH.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON report."),
    stage: str = typer.Option(DEFAULT_STAGE, "--stage", help="Validation stage cutoff."),
    fail_on_warning: bool = typer.Option(False, "--fail-on-warning", help="Fail when warnings exist."),
    expand_parametric: bool = typer.Option(
        False,
        "--expand-parametric",
        help="Expand Parametric:* objects before validation.",
    ),
    parametric_run: int | None = typer.Option(
        None,
        "--parametric-run",
        min=1,
        help="1-based parametric run index used with --expand-parametric.",
    ),
) -> None:
    if schema_path is None:
        raise typer.BadParameter(
            f"Schema path is required. Pass --schema-path or set {SCHEMA_PATH_ENVVAR}.",
            param_hint="--schema-path",
        )
    if stage not in VALID_STAGES:
        raise typer.BadParameter(f"Unsupported stage '{stage}'. Expected one of {', '.join(VALID_STAGES)}.")
    if parametric_run is not None and not expand_parametric:
        raise typer.BadParameter("--parametric-run requires --expand-parametric.", param_hint="--parametric-run")

    try:
        report = validate_file(
            path,
            schema_path=schema_path,
            stage=stage,
            expand_parametric=expand_parametric,
            parametric_run=parametric_run,
        ).to_dict()
    except (EPJSONLoadError, ParametricExpansionError) as exc:
        raise typer.BadParameter(str(exc), param_hint="PATH") from exc
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo(_render_human_report(report))
    raise typer.Exit(code=_exit_code(report, fail_on_warning))


@app.command()
def inspect(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to epJSON file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    try:
        loaded = load_epjson(path)
    except EPJSONLoadError as exc:
        raise typer.BadParameter(str(exc), param_hint="PATH") from exc
    info = inspect_data(loaded.data)
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
) -> None:
    try:
        loaded = load_epjson(path)
    except EPJSONLoadError as exc:
        raise typer.BadParameter(str(exc), param_hint="PATH") from exc
    info = inspect_data(loaded.data)
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


@app.command("hvac-graph")
def hvac_graph(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to epJSON file."),
    graph: str = typer.Option("all", "--graph", help="Graph family: air, plant, zone, or all."),
    output_format: str = typer.Option("text", "--format", help="Output format: text or html."),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output file path for html. If omitted, output is written to stdout.",
    ),
    expand_parametric: bool = typer.Option(
        False,
        "--expand-parametric",
        help="Expand Parametric:* objects before graph extraction.",
    ),
    parametric_run: int | None = typer.Option(
        None,
        "--parametric-run",
        min=1,
        help="1-based parametric run index used with --expand-parametric.",
    ),
) -> None:
    if graph not in {"air", "plant", "zone", "all"}:
        raise typer.BadParameter("Unsupported graph. Expected one of air, plant, zone, all.", param_hint="--graph")
    if output_format not in {"text", "html"}:
        raise typer.BadParameter("Unsupported format. Expected one of text, html.", param_hint="--format")
    if parametric_run is not None and not expand_parametric:
        raise typer.BadParameter("--parametric-run requires --expand-parametric.", param_hint="--parametric-run")

    try:
        loaded = load_epjson(path)
        data = loaded.data
        if expand_parametric:
            data = expand_parametric_data(data, run_index=parametric_run).data
    except (EPJSONLoadError, ParametricExpansionError) as exc:
        raise typer.BadParameter(str(exc), param_hint="PATH") from exc

    diagrams = extract_hvac_diagrams(data)
    if output_format == "text":
        typer.echo(render_diagrams_text(diagrams, graph))
        return

    rendered = render_diagrams_html(diagrams, graph)
    if output is None:
        typer.echo(rendered)
        return
    output.write_text(rendered, encoding="utf-8")
    typer.echo(f"Wrote {output_format.upper()} to {output}")
