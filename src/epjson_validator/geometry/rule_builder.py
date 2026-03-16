"""Build geometry extraction rules from raw schemas."""

from __future__ import annotations

from typing import Any

from epjson_validator.geometry.rules import GeometryCategoryRule, GeometryRules
from epjson_validator.schema.introspection import extract_field_schemas, extract_object_entries

_PARENT_FIELD_CANDIDATES = (
    "building_surface_name",
    "base_surface_name",
    "outside_boundary_condition_object",
)


def build_geometry_rules(raw_schema: dict[str, Any]) -> GeometryRules:
    rules = GeometryRules()
    for category_name, category_schema in extract_object_entries(raw_schema).items():
        field_schemas = extract_field_schemas(category_schema)
        if "vertices" not in field_schemas:
            continue
        parent_fields = tuple(name for name in _PARENT_FIELD_CANDIDATES if name in field_schemas)
        containment_parent_field = "building_surface_name" if "building_surface_name" in field_schemas else None
        rules.categories[category_name] = GeometryCategoryRule(
            category=category_name,
            vertices_field="vertices",
            parent_fields=parent_fields,
            containment_parent_field=containment_parent_field,
            zone_field="zone_name" if "zone_name" in field_schemas else None,
            surface_type_field="surface_type" if "surface_type" in field_schemas else None,
        )
    return rules
