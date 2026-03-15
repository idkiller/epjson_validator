from __future__ import annotations

import json

from typer.testing import CliRunner

from epjson_validator.cli import app
from epjson_validator.loader import detect_version
from epjson_validator.pipeline.validate import validate_data

runner = CliRunner()


def make_valid_model() -> dict:
    return {
        "Version": {
            "Version 1": {
                "version_identifier": "24.2.0",
            }
        },
        "Zone": {
            "ZoneA": {}
        },
        "Material": {
            "Mat1": {
                "roughness": "Smooth",
                "thickness": 0.1,
            }
        },
        "Construction": {
            "Cons1": {
                "materials": ["Mat1"],
            }
        },
        "BuildingSurface:Detailed": {
            "Floor1": {
                "surface_type": "Floor",
                "zone_name": "ZoneA",
                "construction_name": "Cons1",
                "vertices": [
                    {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
                    {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
                    {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.0},
                    {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.0},
                ],
            }
        },
    }


def test_valid_minimal_epjson() -> None:
    report = validate_data(make_valid_model())
    assert report.summary["error_count"] == 0
    assert report.summary["warning_count"] == 0
    assert report.summary["unsupported_count"] == 0
    assert report.ok is True


def test_version_detection() -> None:
    assert detect_version(make_valid_model()) == "24.2.0"


def test_unsupported_version() -> None:
    model = make_valid_model()
    model["Version"]["Version 1"]["version_identifier"] = "23.1.0"
    report = validate_data(model)
    assert any(issue.code == "UNSUPPORTED" for issue in report.issues)
    assert report.ok is False


def test_missing_required_field() -> None:
    model = make_valid_model()
    del model["BuildingSurface:Detailed"]["Floor1"]["construction_name"]
    report = validate_data(model, stage="schema")
    assert any(issue.code == "SCHEMA_ERROR" and issue.path.endswith("construction_name") for issue in report.issues)


def test_missing_zone_reference() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["zone_name"] = "MissingZone"
    report = validate_data(model, stage="reference")
    assert any(issue.code == "REFERENCE_ERROR" and issue.path.endswith("zone_name") for issue in report.issues)


def test_missing_surface_reference() -> None:
    model = make_valid_model()
    model["FenestrationSurface:Detailed"] = {
        "Window1": {
            "building_surface_name": "MissingSurface",
            "construction_name": "Cons1",
            "vertices": [
                {"vertex_x_coordinate": 1.0, "vertex_y_coordinate": 1.0, "vertex_z_coordinate": 0.0},
                {"vertex_x_coordinate": 2.0, "vertex_y_coordinate": 1.0, "vertex_z_coordinate": 0.0},
                {"vertex_x_coordinate": 2.0, "vertex_y_coordinate": 2.0, "vertex_z_coordinate": 0.0},
            ],
        }
    }
    report = validate_data(model, stage="reference")
    assert any(issue.code == "REFERENCE_ERROR" and issue.path.endswith("building_surface_name") for issue in report.issues)


def test_invalid_vertex_count() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 1.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, stage="geometry")
    assert any(issue.code == "GEOMETRY_ERROR" and "at least 3 vertices" in issue.message for issue in report.issues)


def test_zero_area_polygon() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 1.0, "vertex_y_coordinate": 1.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 2.0, "vertex_y_coordinate": 2.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, stage="geometry")
    assert any(issue.code == "GEOMETRY_ERROR" and "area is zero" in issue.message for issue in report.issues)


def test_non_planar_polygon_warning() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.2},
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, stage="geometry")
    assert any(issue.code == "GEOMETRY_WARNING" and "approximately planar" in issue.message for issue in report.issues)


def test_visualization_warnings() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["surface_type"] = "Wall"
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 3.0},
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 3.0},
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, stage="visualization", profile="svg-plan")
    assert any(issue.code == "VIS_WARNING" for issue in report.issues)


def test_cli_json_output(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    model_path.write_text(json.dumps(make_valid_model()), encoding="utf-8")
    result = runner.invoke(app, ["validate", str(model_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ep_version"] == "24.2.0"
    assert "summary" in payload
    assert payload["summary"]["error_count"] == 0
