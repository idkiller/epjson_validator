from __future__ import annotations

import json

from typer.testing import CliRunner

from epjson_validator.cli import app
from epjson_validator.config import SCHEMA_PATH_ENVVAR
from epjson_validator.loader import detect_version
from epjson_validator.pipeline.validate import validate_data

runner = CliRunner()


def make_raw_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "Version": {
                "type": "object",
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["version_identifier"],
                        "properties": {
                            "version_identifier": {
                                "type": "string",
                                "default": "24.2.0",
                            }
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "Zone": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["ZoneNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    }
                },
            },
            "Material": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["MaterialNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["roughness", "thickness"],
                        "properties": {
                            "roughness": {
                                "type": "string",
                                "enum": ["Smooth", "Rough"],
                            },
                            "thickness": {
                                "type": "number",
                            },
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "Construction": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["ConstructionNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["materials"],
                        "properties": {
                            "materials": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "object_list": ["MaterialNames"],
                                },
                            }
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "BuildingSurface:Detailed": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["SurfaceNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["surface_type", "construction_name", "zone_name", "vertices"],
                        "properties": {
                            "surface_type": {
                                "type": "string",
                                "enum": ["Floor", "Wall", "Roof", "Ceiling"],
                            },
                            "construction_name": {
                                "type": "string",
                                "object_list": ["ConstructionNames"],
                            },
                            "zone_name": {
                                "type": "string",
                                "object_list": ["ZoneNames"],
                            },
                            "outside_boundary_condition_object": {
                                "type": "string",
                                "object_list": ["SurfaceNames"],
                            },
                            "vertices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "vertex_x_coordinate",
                                        "vertex_y_coordinate",
                                        "vertex_z_coordinate",
                                    ],
                                    "properties": {
                                        "vertex_x_coordinate": {"type": "number"},
                                        "vertex_y_coordinate": {"type": "number"},
                                        "vertex_z_coordinate": {"type": "number"},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "FenestrationSurface:Detailed": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["SurfaceNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["building_surface_name", "construction_name", "vertices"],
                        "properties": {
                            "building_surface_name": {
                                "type": "string",
                                "object_list": ["SurfaceNames"],
                            },
                            "construction_name": {
                                "type": "string",
                                "object_list": ["ConstructionNames"],
                            },
                            "surface_type": {
                                "type": "string",
                                "enum": ["Window", "Door"],
                            },
                            "vertices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "vertex_x_coordinate",
                                        "vertex_y_coordinate",
                                        "vertex_z_coordinate",
                                    ],
                                    "properties": {
                                        "vertex_x_coordinate": {"type": "number"},
                                        "vertex_y_coordinate": {"type": "number"},
                                        "vertex_z_coordinate": {"type": "number"},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "AirLoopHVAC:OutdoorAirSystem:EquipmentList": {
                "type": "object",
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "required": ["component_1_object_type", "component_1_name"],
                        "properties": {
                            "component_1_object_type": {
                                "type": "string",
                                "enum": ["Coil:Heating:Water", "OutdoorAir:Mixer"],
                                "object_list": ["validOASysEquipmentTypes"],
                            },
                            "component_1_name": {
                                "type": "string",
                                "object_list": ["validOASysEquipmentNames"],
                            },
                        },
                        "additionalProperties": False,
                    }
                },
            },
            "Coil:Heating:Water": {
                "type": "object",
                "name": {
                    "type": "string",
                    "reference": ["validOASysEquipmentNames"],
                },
                "patternProperties": {
                    "^.*\\S.*$": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    }
                },
            },
        },
    }


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
    report = validate_data(make_valid_model(), raw_schema=make_raw_schema())
    assert report.summary["error_count"] == 0
    assert report.summary["warning_count"] == 0
    assert report.summary["unsupported_count"] == 0
    assert report.ok is True


def test_version_detection() -> None:
    assert detect_version(make_valid_model()) == "24.2.0"


def test_missing_required_field() -> None:
    model = make_valid_model()
    del model["BuildingSurface:Detailed"]["Floor1"]["construction_name"]
    report = validate_data(model, raw_schema=make_raw_schema(), stage="schema")
    assert any(issue.code == "SCHEMA_ERROR" and issue.path == "BuildingSurface:Detailed.Floor1.construction_name" for issue in report.issues)


def test_missing_zone_reference() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["zone_name"] = "MissingZone"
    report = validate_data(model, raw_schema=make_raw_schema(), stage="reference")
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
    report = validate_data(model, raw_schema=make_raw_schema(), stage="reference")
    assert any(issue.code == "REFERENCE_ERROR" and issue.path.endswith("building_surface_name") for issue in report.issues)


def test_reference_names_are_case_insensitive() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["zone_name"] = "zonea"
    report = validate_data(model, raw_schema=make_raw_schema(), stage="reference")
    assert not any(issue.code == "REFERENCE_ERROR" for issue in report.issues)


def test_object_type_namespace_is_not_treated_as_object_reference() -> None:
    model = make_valid_model()
    model["Coil:Heating:Water"] = {
        "OA Heating Coil 1": {},
    }
    model["AirLoopHVAC:OutdoorAirSystem:EquipmentList"] = {
        "OA Sys 1 Equipment": {
            "component_1_object_type": "Coil:Heating:Water",
            "component_1_name": "OA Heating Coil 1",
        }
    }
    report = validate_data(model, raw_schema=make_raw_schema(), stage="reference")
    assert not any(
        issue.code == "REFERENCE_ERROR"
        and issue.path == "AirLoopHVAC:OutdoorAirSystem:EquipmentList.OA Sys 1 Equipment.component_1_object_type"
        for issue in report.issues
    )


def test_invalid_vertex_count() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 1.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, raw_schema=make_raw_schema(), stage="geometry")
    assert any(issue.code == "GEOMETRY_ERROR" and "at least 3 vertices" in issue.message for issue in report.issues)


def test_zero_area_polygon() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 1.0, "vertex_y_coordinate": 1.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 2.0, "vertex_y_coordinate": 2.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, raw_schema=make_raw_schema(), stage="geometry")
    assert any(issue.code == "GEOMETRY_ERROR" and "area is zero" in issue.message for issue in report.issues)


def test_non_planar_polygon_warning() -> None:
    model = make_valid_model()
    model["BuildingSurface:Detailed"]["Floor1"]["vertices"] = [
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 0.0, "vertex_z_coordinate": 0.0},
        {"vertex_x_coordinate": 4.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.2},
        {"vertex_x_coordinate": 0.0, "vertex_y_coordinate": 4.0, "vertex_z_coordinate": 0.0},
    ]
    report = validate_data(model, raw_schema=make_raw_schema(), stage="geometry")
    assert any(issue.code == "GEOMETRY_WARNING" and "approximately planar" in issue.message for issue in report.issues)


def test_cli_json_output(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    schema_path = tmp_path / "Energy+.schema.epJSON"
    model_path.write_text(json.dumps(make_valid_model()), encoding="utf-8")
    schema_path.write_text(json.dumps(make_raw_schema()), encoding="utf-8")

    result = runner.invoke(app, ["validate", str(model_path), "--schema-path", str(schema_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ep_version"] == "24.2.0"
    assert "summary" in payload
    assert payload["summary"]["error_count"] == 0


def test_cli_uses_schema_path_envvar(tmp_path, monkeypatch) -> None:
    model_path = tmp_path / "model.epJSON"
    schema_path = tmp_path / "Energy+.schema.epJSON"
    model_path.write_text(json.dumps(make_valid_model()), encoding="utf-8")
    schema_path.write_text(json.dumps(make_raw_schema()), encoding="utf-8")
    monkeypatch.setenv(SCHEMA_PATH_ENVVAR, str(schema_path))

    result = runner.invoke(app, ["validate", str(model_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["error_count"] == 0


def test_cli_requires_schema_path(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    model_path.write_text(json.dumps(make_valid_model()), encoding="utf-8")

    result = runner.invoke(app, ["validate", str(model_path)])
    assert result.exit_code != 0


def test_cli_rejects_idf_input(tmp_path) -> None:
    model_path = tmp_path / "model.idf"
    schema_path = tmp_path / "Energy+.schema.epJSON"
    model_path.write_text("Version,24.2;", encoding="utf-8")
    schema_path.write_text(json.dumps(make_raw_schema()), encoding="utf-8")

    result = runner.invoke(app, ["validate", str(model_path), "--schema-path", str(schema_path)])
    assert result.exit_code != 0
    assert "epJSON" in result.stderr
    assert "IDF" in result.stderr
