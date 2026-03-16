"""Manually curated EnergyPlus 24.2.x schema provider."""

from __future__ import annotations

from epjson_validator.models import FieldSchema, ObjectSchema, VersionSchema


STRING = "string"
NUMBER = "number"
ARRAY = "array"
VERTICES = "vertices"

SUPPORTED_EP_VERSIONS = ("24.1.0", "24.2.0")


def get_schema(ep_version: str = "24.2.0") -> VersionSchema:
    return VersionSchema(
        ep_version=ep_version,
        objects={
            "Version": ObjectSchema(
                name="Version",
                fields={
                    "version_identifier": FieldSchema("version_identifier", STRING, required=True),
                },
                allow_additional_fields=False,
            ),
            "GlobalGeometryRules": ObjectSchema(
                name="GlobalGeometryRules",
                fields={
                    "coordinate_system": FieldSchema(
                        "coordinate_system",
                        STRING,
                        enum_values=["Relative", "World"],
                    ),
                    "starting_vertex_position": FieldSchema(
                        "starting_vertex_position",
                        STRING,
                        enum_values=["UpperLeftCorner", "LowerLeftCorner", "UpperRightCorner", "LowerRightCorner"],
                    ),
                    "vertex_entry_direction": FieldSchema(
                        "vertex_entry_direction",
                        STRING,
                        enum_values=["Clockwise", "Counterclockwise"],
                    ),
                },
                allow_additional_fields=False,
            ),
            "Zone": ObjectSchema(
                name="Zone",
                fields={
                    "direction_of_relative_north": FieldSchema("direction_of_relative_north", NUMBER),
                },
                allow_additional_fields=False,
            ),
            "BuildingSurface:Detailed": ObjectSchema(
                name="BuildingSurface:Detailed",
                fields={
                    "surface_type": FieldSchema(
                        "surface_type",
                        STRING,
                        required=True,
                        enum_values=["Wall", "Roof", "Floor", "Ceiling"],
                    ),
                    "zone_name": FieldSchema("zone_name", STRING, required=True, reference_target="Zone"),
                    "construction_name": FieldSchema(
                        "construction_name",
                        STRING,
                        required=True,
                        reference_target="Construction",
                    ),
                    "outside_boundary_condition_object": FieldSchema(
                        "outside_boundary_condition_object",
                        STRING,
                        reference_target="BuildingSurface:Detailed",
                        semantic_type="parent_surface",
                    ),
                    "vertices": FieldSchema("vertices", VERTICES, required=True, item_type="object"),
                },
                geometry_supported=True,
                visualization_supported=True,
                allow_additional_fields=False,
            ),
            "FenestrationSurface:Detailed": ObjectSchema(
                name="FenestrationSurface:Detailed",
                fields={
                    "surface_type": FieldSchema(
                        "surface_type",
                        STRING,
                        enum_values=["Window", "Door", "GlassDoor", "Skylight"],
                    ),
                    "building_surface_name": FieldSchema(
                        "building_surface_name",
                        STRING,
                        required=True,
                        reference_target="BuildingSurface:Detailed",
                        semantic_type="parent_surface",
                    ),
                    "construction_name": FieldSchema(
                        "construction_name",
                        STRING,
                        required=True,
                        reference_target="Construction",
                    ),
                    "vertices": FieldSchema("vertices", VERTICES, required=True, item_type="object"),
                },
                geometry_supported=True,
                visualization_supported=True,
                allow_additional_fields=False,
            ),
            "Shading:Zone:Detailed": ObjectSchema(
                name="Shading:Zone:Detailed",
                fields={
                    "base_surface_name": FieldSchema(
                        "base_surface_name",
                        STRING,
                        reference_target="BuildingSurface:Detailed",
                    ),
                    "vertices": FieldSchema("vertices", VERTICES, required=True, item_type="object"),
                },
                geometry_supported=True,
                visualization_supported=False,
                allow_additional_fields=False,
            ),
            "Shading:Building:Detailed": ObjectSchema(
                name="Shading:Building:Detailed",
                fields={
                    "vertices": FieldSchema("vertices", VERTICES, required=True, item_type="object"),
                },
                geometry_supported=True,
                visualization_supported=False,
                allow_additional_fields=False,
            ),
            "Shading:Site:Detailed": ObjectSchema(
                name="Shading:Site:Detailed",
                fields={
                    "vertices": FieldSchema("vertices", VERTICES, required=True, item_type="object"),
                },
                geometry_supported=True,
                visualization_supported=False,
                allow_additional_fields=False,
            ),
            "Construction": ObjectSchema(
                name="Construction",
                fields={
                    "materials": FieldSchema(
                        "materials",
                        ARRAY,
                        required=True,
                        reference_target="Material",
                        item_type="string",
                    ),
                },
                allow_additional_fields=False,
            ),
            "Material": ObjectSchema(
                name="Material",
                fields={
                    "roughness": FieldSchema(
                        "roughness",
                        STRING,
                        required=True,
                        enum_values=[
                            "VeryRough",
                            "Rough",
                            "MediumRough",
                            "MediumSmooth",
                            "Smooth",
                            "VerySmooth",
                        ],
                    ),
                    "thickness": FieldSchema("thickness", NUMBER, required=True),
                },
                allow_additional_fields=False,
            ),
        },
    )
