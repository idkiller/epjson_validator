import json

from typer.testing import CliRunner

from epjson_validator.cli import app
from epjson_validator.schema.converter.convert import convert_raw_schema, version_schema_to_dict

runner = CliRunner()


def _make_raw_schema() -> dict:
    return {
        "properties": {
            "Zone": {
                "patternProperties": {
                    ".*": {
                        "type": "object",
                        "required": ["direction_of_relative_north"],
                        "properties": {
                            "direction_of_relative_north": {"type": "number"},
                        },
                    }
                }
            },
            "BuildingSurface:Detailed": {
                "patternProperties": {
                    ".*": {
                        "type": "object",
                        "required": ["surface_type", "zone_name", "vertices"],
                        "properties": {
                            "surface_type": {"type": "string", "enum": ["Wall", "Floor"]},
                            "zone_name": {"type": "string", "object_list": "ZoneNames"},
                            "vertices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                },
                            },
                        },
                    }
                }
            },
        },
        "object_lists": {
            "ZoneNames": {
                "class_reference": "Zone",
            }
        },
    }


def test_convert_raw_schema_extracts_categories_and_fields() -> None:
    version_schema = convert_raw_schema(_make_raw_schema(), ep_version="24.2.0")

    assert "Zone" in version_schema.objects
    assert "BuildingSurface:Detailed" in version_schema.objects

    building_schema = version_schema.objects["BuildingSurface:Detailed"]
    assert building_schema.geometry_supported is True
    assert building_schema.visualization_supported is True

    zone_name = building_schema.fields["zone_name"]
    assert zone_name.field_type == "string"
    assert zone_name.reference_target == "Zone"

    vertices = building_schema.fields["vertices"]
    assert vertices.field_type == "vertices"
    assert vertices.item_type == "object"

    surface_type = building_schema.fields["surface_type"]
    assert surface_type.enum_values == ["Wall", "Floor"]
    assert surface_type.required is True


def test_version_schema_to_dict_shape() -> None:
    version_schema = convert_raw_schema(_make_raw_schema(), ep_version="24.2.0")
    payload = version_schema_to_dict(version_schema)

    assert payload["ep_version"] == "24.2.0"
    assert payload["objects"]["BuildingSurface:Detailed"]["fields"]["vertices"]["field_type"] == "vertices"


def test_convert_raw_schema_raises_on_missing_categories() -> None:
    raw_schema = {"properties": {"epjson_version": {"type": "string"}}}

    try:
        convert_raw_schema(raw_schema)
    except ValueError as exc:
        assert "No object categories" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing object categories")


def test_cli_convert_schema_json_output(tmp_path) -> None:
    raw_path = tmp_path / "Energy+.schema.epJSON"
    raw_path.write_text(json.dumps(_make_raw_schema()), encoding="utf-8")

    result = runner.invoke(app, ["convert-schema", str(raw_path), "--ep-version", "24.2.0"])
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["ep_version"] == "24.2.0"
    assert "Zone" in payload["objects"]


def test_cli_convert_schema_writes_output_file(tmp_path) -> None:
    raw_path = tmp_path / "Energy+.schema.epJSON"
    out_path = tmp_path / "generated" / "provider_schema.json"
    raw_path.write_text(json.dumps(_make_raw_schema()), encoding="utf-8")

    result = runner.invoke(app, ["convert-schema", str(raw_path), "-o", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["objects"]["Zone"]["fields"]["direction_of_relative_north"]["required"] is True
