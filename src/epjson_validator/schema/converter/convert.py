"""Convert a raw EnergyPlus schema into the internal schema model."""

from __future__ import annotations

from typing import Any

from epjson_validator.models import FieldSchema, ObjectSchema, VersionSchema
from epjson_validator.schema.converter.enrich import enrich_raw_schema

SIMPLE_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "real": "number",
    "integer": "integer",
    "int": "integer",
    "boolean": "boolean",
    "array": "array",
    "object": "object",
}

GEOMETRY_CATEGORIES = {
    "BuildingSurface:Detailed",
    "FenestrationSurface:Detailed",
    "Shading:Zone:Detailed",
    "Shading:Building:Detailed",
    "Shading:Site:Detailed",
}

VISUALIZATION_CATEGORIES = {"BuildingSurface:Detailed", "FenestrationSurface:Detailed"}



def convert_raw_schema(raw_schema: dict[str, Any], *, ep_version: str = "24.2.0") -> VersionSchema:
    """Convert EnergyPlus `Energy+.schema.epJSON` style JSON into `VersionSchema`.

    The converter is tolerant to minor schema shape differences between versions,
    and focuses on extracting categories + field definitions used by this validator.
    """

    enriched = enrich_raw_schema(raw_schema)
    object_lists = _extract_object_lists(enriched)

    object_entries = _extract_object_entries(enriched)
    if not object_entries:
        raise ValueError("No object categories were found in the raw schema.")

    objects: dict[str, ObjectSchema] = {}
    for category_name, category_schema in object_entries.items():
        fields = _convert_category_fields(category_schema, object_lists)
        objects[category_name] = ObjectSchema(
            name=category_name,
            fields=fields,
            geometry_supported=category_name in GEOMETRY_CATEGORIES,
            visualization_supported=category_name in VISUALIZATION_CATEGORIES,
            allow_additional_fields=True,
        )

    return VersionSchema(ep_version=ep_version, objects=objects)




def version_schema_to_dict(schema: VersionSchema) -> dict[str, Any]:
    """Serialize `VersionSchema` dataclasses into JSON-friendly dictionaries."""

    return {
        "ep_version": schema.ep_version,
        "objects": {
            object_name: {
                "name": object_schema.name,
                "geometry_supported": object_schema.geometry_supported,
                "visualization_supported": object_schema.visualization_supported,
                "allow_additional_fields": object_schema.allow_additional_fields,
                "fields": {
                    field_name: {
                        "name": field.name,
                        "field_type": field.field_type,
                        "required": field.required,
                        "enum_values": field.enum_values,
                        "reference_target": field.reference_target,
                        "semantic_type": field.semantic_type,
                        "item_type": field.item_type,
                    }
                    for field_name, field in object_schema.fields.items()
                },
            }
            for object_name, object_schema in schema.objects.items()
        },
    }


def _extract_object_lists(raw_schema: dict[str, Any]) -> dict[str, str]:
    lists = raw_schema.get("object_lists")
    if not isinstance(lists, dict):
        return {}

    mapping: dict[str, str] = {}
    for list_name, payload in lists.items():
        if not isinstance(payload, dict):
            continue
        if "class_reference" in payload and isinstance(payload["class_reference"], str):
            mapping[list_name] = payload["class_reference"]
            continue
        ref_class = payload.get("reference")
        if isinstance(ref_class, dict):
            category = ref_class.get("class_name")
            if isinstance(category, str):
                mapping[list_name] = category
    return mapping



def _extract_object_entries(raw_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    properties = raw_schema.get("properties")
    if not isinstance(properties, dict):
        return {}

    entries: dict[str, dict[str, Any]] = {}
    for key, value in properties.items():
        if key in {"epjson_version", "schema_version"}:
            continue
        if isinstance(value, dict):
            entries[key] = value
    return entries



def _convert_category_fields(category_schema: dict[str, Any], object_lists: dict[str, str]) -> dict[str, FieldSchema]:
    object_schema = _resolve_object_instance_schema(category_schema)
    if not object_schema:
        return {}

    raw_fields = object_schema.get("properties")
    if not isinstance(raw_fields, dict):
        return {}

    required_fields = set(_as_str_list(object_schema.get("required")))

    fields: dict[str, FieldSchema] = {}
    for field_name, field_schema in raw_fields.items():
        if not isinstance(field_schema, dict):
            continue
        fields[field_name] = _to_field_schema(
            field_name,
            field_schema,
            required=(field_name in required_fields),
            object_lists=object_lists,
        )
    return fields



def _resolve_object_instance_schema(category_schema: dict[str, Any]) -> dict[str, Any] | None:
    pattern_props = category_schema.get("patternProperties")
    if isinstance(pattern_props, dict):
        for pattern_schema in pattern_props.values():
            if isinstance(pattern_schema, dict) and isinstance(pattern_schema.get("properties"), dict):
                return pattern_schema

    additional = category_schema.get("additionalProperties")
    if isinstance(additional, dict) and isinstance(additional.get("properties"), dict):
        return additional

    if isinstance(category_schema.get("properties"), dict):
        return category_schema

    return None



def _to_field_schema(
    field_name: str,
    raw_field: dict[str, Any],
    *,
    required: bool,
    object_lists: dict[str, str],
) -> FieldSchema:
    field_type = _determine_field_type(field_name, raw_field)
    enum_values = _as_str_list(raw_field.get("enum")) or None
    reference_target = _extract_reference_target(raw_field, object_lists)
    item_type = _extract_item_type(raw_field)

    return FieldSchema(
        name=field_name,
        field_type=field_type,
        required=required,
        enum_values=enum_values,
        reference_target=reference_target,
        item_type=item_type,
    )



def _determine_field_type(field_name: str, raw_field: dict[str, Any]) -> str:
    if field_name == "vertices":
        return "vertices"

    raw_type = raw_field.get("type")
    if isinstance(raw_type, list):
        raw_type = next((t for t in raw_type if t != "null"), raw_type[0] if raw_type else None)

    if isinstance(raw_type, str):
        return SIMPLE_TYPE_MAP.get(raw_type.lower(), "string")

    data_type = raw_field.get("data_type")
    if isinstance(data_type, str):
        lowered = data_type.lower()
        if lowered in SIMPLE_TYPE_MAP:
            return SIMPLE_TYPE_MAP[lowered]
        if lowered in {"real", "double"}:
            return "number"

    if isinstance(raw_field.get("items"), dict):
        return "array"

    return "string"



def _extract_reference_target(raw_field: dict[str, Any], object_lists: dict[str, str]) -> str | None:
    object_list_name = raw_field.get("object_list")
    if isinstance(object_list_name, str) and object_list_name in object_lists:
        return object_lists[object_list_name]

    if isinstance(raw_field.get("reference"), str):
        return raw_field["reference"]

    return None



def _extract_item_type(raw_field: dict[str, Any]) -> str | None:
    items = raw_field.get("items")
    if not isinstance(items, dict):
        return None

    item_type = items.get("type")
    if isinstance(item_type, str):
        return SIMPLE_TYPE_MAP.get(item_type.lower(), item_type.lower())

    return None



def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
