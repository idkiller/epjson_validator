from __future__ import annotations

import json

from typer.testing import CliRunner

from epjson_validator.cli import app

runner = CliRunner()


def make_hvac_model() -> dict:
    return {
        "AirLoopHVAC": {
            "Main Air Loop": {
                "branch_list_name": "Main Air Loop Branches",
            }
        },
        "AirLoopHVAC:OutdoorAirSystem": {
            "OA Sys 1": {
                "outdoor_air_equipment_list_name": "OA Sys 1 Equipment",
            }
        },
        "AirLoopHVAC:OutdoorAirSystem:EquipmentList": {
            "OA Sys 1 Equipment": {
                "component_1_object_type": "Coil:Heating:Water",
                "component_1_name": "OA Heating Coil 1",
                "component_2_object_type": "OutdoorAir:Mixer",
                "component_2_name": "OA Mixer 1",
            }
        },
        "Branch": {
            "Main Air Branch": {
                "components": [
                    {
                        "component_object_type": "AirLoopHVAC:OutdoorAirSystem",
                        "component_name": "OA Sys 1",
                    },
                    {
                        "component_object_type": "Fan:VariableVolume",
                        "component_name": "Supply Fan 1",
                    },
                ]
            },
            "Cooling Supply Branch": {
                "components": [
                    {
                        "component_object_type": "Pump:VariableSpeed",
                        "component_name": "CW Pump",
                    }
                ]
            },
            "Cooling Demand Branch": {
                "components": [
                    {
                        "component_object_type": "Coil:Cooling:Water",
                        "component_name": "Main Cooling Coil 1",
                    }
                ]
            },
        },
        "BranchList": {
            "Main Air Loop Branches": {
                "branches": [{"branch_name": "Main Air Branch"}],
            },
            "Cooling Supply Branches": {
                "branches": [{"branch_name": "Cooling Supply Branch"}],
            },
            "Cooling Demand Branches": {
                "branches": [{"branch_name": "Cooling Demand Branch"}],
            },
        },
        "PlantLoop": {
            "Chilled Water Loop": {
                "plant_side_branch_list_name": "Cooling Supply Branches",
                "demand_side_branch_list_name": "Cooling Demand Branches",
            }
        },
        "ZoneHVAC:EquipmentConnections": {
            "ZoneHVAC:EquipmentConnections 1": {
                "zone_name": "SPACE1-1",
                "zone_conditioning_equipment_list_name": "SPACE1-1 Eq",
            }
        },
        "ZoneHVAC:EquipmentList": {
            "SPACE1-1 Eq": {
                "equipment": [
                    {
                        "zone_equipment_object_type": "ZoneHVAC:AirDistributionUnit",
                        "zone_equipment_name": "SPACE1-1 ATU",
                    }
                ]
            }
        },
        "ZoneHVAC:AirDistributionUnit": {
            "SPACE1-1 ATU": {
                "air_terminal_object_type": "AirTerminal:SingleDuct:VAV:Reheat",
                "air_terminal_name": "SPACE1-1 VAV Reheat",
            }
        },
        "AirTerminal:SingleDuct:VAV:Reheat": {
            "SPACE1-1 VAV Reheat": {
                "reheat_coil_object_type": "Coil:Heating:Water",
                "reheat_coil_name": "SPACE1-1 Zone Coil",
            }
        },
    }


def test_hvac_graph_text_output(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    model_path.write_text(json.dumps(make_hvac_model()), encoding="utf-8")

    result = runner.invoke(app, ["hvac-graph", str(model_path), "--graph", "all"])
    assert result.exit_code == 0
    assert "AIR LOOP GRAPHS" in result.stdout
    assert "Main Air Loop" in result.stdout
    assert "OA Heating Coil 1" in result.stdout
    assert "PLANT LOOP GRAPHS" in result.stdout
    assert "ZONE EQUIPMENT GRAPHS" in result.stdout



def test_hvac_graph_html_output(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    html_path = tmp_path / "graph.html"
    model_path.write_text(json.dumps(make_hvac_model()), encoding="utf-8")

    result = runner.invoke(
        app,
        ["hvac-graph", str(model_path), "--graph", "air", "--format", "html", "--output", str(html_path)],
    )
    assert result.exit_code == 0
    assert html_path.exists()
    payload = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in payload
    assert '<section class="diagram">' in payload
    assert "AIR LOOP GRAPHS" in payload
    assert "Legend (current loop)" not in payload
    assert "OA Heating Coil 1" in payload
    assert ".node{" in payload
    assert "max-width:100px" in payload
    assert "text-overflow:ellipsis" in payload
    assert "overflow:hidden" in payload
    assert "white-space:nowrap" in payload
    assert "direction:rtl" in payload


def test_hvac_graph_svg_format_rejected(tmp_path) -> None:
    model_path = tmp_path / "model.epJSON"
    model_path.write_text(json.dumps(make_hvac_model()), encoding="utf-8")

    result = runner.invoke(app, ["hvac-graph", str(model_path), "--format", "svg"])
    assert result.exit_code == 2
