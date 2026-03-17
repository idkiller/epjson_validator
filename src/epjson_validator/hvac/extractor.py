"""Extract simple HVAC connectivity diagrams from epJSON."""

from __future__ import annotations

from typing import Any

from epjson_validator.hvac.models import HVACDiagram


def extract_hvac_diagrams(data: dict[str, Any]) -> dict[str, list[HVACDiagram]]:
    return {
        "air": _extract_air_loop_diagrams(data),
        "plant": _extract_plant_loop_diagrams(data),
        "zone": _extract_zone_equipment_diagrams(data),
    }


def _extract_air_loop_diagrams(data: dict[str, Any]) -> list[HVACDiagram]:
    air_loops = _object_map(data, "AirLoopHVAC")
    branch_lists = _object_map(data, "BranchList")
    branches = _object_map(data, "Branch")
    oa_systems = _object_map(data, "AirLoopHVAC:OutdoorAirSystem")
    oa_equipment_lists = _object_map(data, "AirLoopHVAC:OutdoorAirSystem:EquipmentList")

    diagrams: list[HVACDiagram] = []
    for loop_name, loop_data in air_loops.items():
        diagram = HVACDiagram(name=loop_name, kind="air")
        loop_node = _node_id("air_loop", loop_name)
        diagram.add_node(loop_node, loop_name, "loop")

        branch_list_name = loop_data.get("branch_list_name")
        for branch_name in _branch_names(branch_lists.get(branch_list_name, {})):
            branch_node = _node_id("branch", branch_name)
            diagram.add_node(branch_node, branch_name, "branch")
            path_nodes = [loop_node, branch_node]
            for component in _components(branches.get(branch_name, {})):
                path_nodes.extend(
                    _expand_air_component(
                        diagram,
                        component_object_type=component.get("component_object_type"),
                        component_name=component.get("component_name"),
                        oa_systems=oa_systems,
                        oa_equipment_lists=oa_equipment_lists,
                    )
                )
            diagram.add_path(branch_name, path_nodes)
        diagrams.append(diagram)
    return diagrams


def _extract_plant_loop_diagrams(data: dict[str, Any]) -> list[HVACDiagram]:
    plant_loops = _object_map(data, "PlantLoop")
    branch_lists = _object_map(data, "BranchList")
    branches = _object_map(data, "Branch")

    diagrams: list[HVACDiagram] = []
    for loop_name, loop_data in plant_loops.items():
        diagram = HVACDiagram(name=loop_name, kind="plant")
        loop_node = _node_id("plant_loop", loop_name)
        diagram.add_node(loop_node, loop_name, "loop")

        for side_name, branch_list_field in (
            ("supply", "plant_side_branch_list_name"),
            ("demand", "demand_side_branch_list_name"),
        ):
            branch_list_name = loop_data.get(branch_list_field)
            side_node = _node_id("plant_side", f"{loop_name}:{side_name}")
            diagram.add_node(side_node, f"{side_name.title()} Side", "side")
            for branch_name in _branch_names(branch_lists.get(branch_list_name, {})):
                branch_node = _node_id("branch", f"{loop_name}:{branch_name}")
                diagram.add_node(branch_node, branch_name, "branch")
                path_nodes = [loop_node, side_node, branch_node]
                for component in _components(branches.get(branch_name, {})):
                    component_node = _component_node(
                        diagram,
                        component_object_type=component.get("component_object_type"),
                        component_name=component.get("component_name"),
                    )
                    if component_node:
                        path_nodes.append(component_node)
                diagram.add_path(f"{side_name.title()} | {branch_name}", path_nodes)
        diagrams.append(diagram)
    return diagrams


def _extract_zone_equipment_diagrams(data: dict[str, Any]) -> list[HVACDiagram]:
    connections = _object_map(data, "ZoneHVAC:EquipmentConnections")
    equipment_lists = _object_map(data, "ZoneHVAC:EquipmentList")
    air_distribution_units = _object_map(data, "ZoneHVAC:AirDistributionUnit")

    diagrams: list[HVACDiagram] = []
    for _, connection_data in connections.items():
        zone_name = connection_data.get("zone_name")
        if not isinstance(zone_name, str) or not zone_name:
            continue
        diagram = HVACDiagram(name=zone_name, kind="zone")
        zone_node = _node_id("zone", zone_name)
        diagram.add_node(zone_node, zone_name, "zone")

        equipment_list_name = connection_data.get("zone_conditioning_equipment_list_name")
        equipment_list_node = _node_id("zone_list", equipment_list_name or f"{zone_name}:equipment")
        diagram.add_node(
            equipment_list_node,
            equipment_list_name or "unknown",
            "list",
        )

        equipment_list = equipment_lists.get(equipment_list_name, {})
        for equipment in equipment_list.get("equipment", []):
            if not isinstance(equipment, dict):
                continue
            equipment_type = equipment.get("zone_equipment_object_type")
            equipment_name = equipment.get("zone_equipment_name")
            path_nodes = [zone_node, equipment_list_node]
            equipment_node = _component_node(diagram, equipment_type, equipment_name)
            if equipment_node:
                path_nodes.append(equipment_node)

            if equipment_type == "ZoneHVAC:AirDistributionUnit":
                unit_data = air_distribution_units.get(equipment_name, {})
                terminal_node = _component_node(
                    diagram,
                    unit_data.get("air_terminal_object_type"),
                    unit_data.get("air_terminal_name"),
                )
                if terminal_node:
                    path_nodes.append(terminal_node)
                    reheat_type = unit_data.get("reheat_coil_object_type")
                    reheat_name = unit_data.get("reheat_coil_name")
                    # Most terminals carry the reheat reference, not the ADU itself.
                    terminal_data = _object_map(data, str(unit_data.get("air_terminal_object_type"))).get(
                        str(unit_data.get("air_terminal_name")),
                        {},
                    )
                    reheat_type = terminal_data.get("reheat_coil_object_type", reheat_type)
                    reheat_name = terminal_data.get("reheat_coil_name", reheat_name)
                    reheat_node = _component_node(diagram, reheat_type, reheat_name)
                    if reheat_node:
                        path_nodes.append(reheat_node)

            label = f"{equipment_type or 'Equipment'} | {equipment_name or 'unknown'}"
            diagram.add_path(label, path_nodes)
        diagrams.append(diagram)
    return diagrams


def _expand_air_component(
    diagram: HVACDiagram,
    *,
    component_object_type: Any,
    component_name: Any,
    oa_systems: dict[str, dict[str, Any]],
    oa_equipment_lists: dict[str, dict[str, Any]],
) -> list[str]:
    component_node = _component_node(diagram, component_object_type, component_name)
    if component_node is None:
        return []
    if component_object_type != "AirLoopHVAC:OutdoorAirSystem":
        return [component_node]

    nodes = [component_node]
    oa_system = oa_systems.get(str(component_name), {})
    equipment_list_name = oa_system.get("outdoor_air_equipment_list_name")
    equipment_list = oa_equipment_lists.get(equipment_list_name, {})
    for index in range(1, 33):
        object_type = equipment_list.get(f"component_{index}_object_type")
        name = equipment_list.get(f"component_{index}_name")
        nested_node = _component_node(diagram, object_type, name)
        if nested_node:
            nodes.append(nested_node)
    return nodes


def _component_node(diagram: HVACDiagram, component_object_type: Any, component_name: Any) -> str | None:
    if not isinstance(component_object_type, str) or not isinstance(component_name, str):
        return None
    node_id = _node_id(component_object_type, component_name)
    diagram.add_node(node_id, component_name, "component")
    return node_id


def _object_map(data: dict[str, Any], category: str) -> dict[str, dict[str, Any]]:
    raw = data.get(category)
    if not isinstance(raw, dict):
        return {}
    return {name: value for name, value in raw.items() if isinstance(value, dict)}


def _branch_names(branch_list_data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in branch_list_data.get("branches", []):
        if not isinstance(item, dict):
            continue
        branch_name = item.get("branch_name")
        if isinstance(branch_name, str) and branch_name:
            names.append(branch_name)
    return names


def _components(branch_data: dict[str, Any]) -> list[dict[str, Any]]:
    components = branch_data.get("components")
    if not isinstance(components, list):
        return []
    return [item for item in components if isinstance(item, dict)]


def _node_id(kind: str, name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    return f"{kind}:{safe}"
