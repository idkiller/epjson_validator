"""Reference validation."""

from __future__ import annotations

from typing import Any

from epjson_validator.diagnostics import IssueCollector
from epjson_validator.reference.models import ReferenceFieldRule, ReferenceIndex


def validate_references(
    data: dict[str, Any],
    reference_index: ReferenceIndex,
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    registry = _build_namespace_registry(data, reference_index, collector, ep_version)

    for category, field_rules in reference_index.fields_by_category.items():
        raw_objects = data.get(category)
        if category == "Version" or not isinstance(raw_objects, dict):
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            for field_name, field_rule in field_rules.items():
                if field_name not in obj:
                    continue
                if _should_skip_reference_validation(category, field_name, obj, data):
                    continue
                value = obj[field_name]
                if field_rule.is_array and isinstance(value, list):
                    _validate_reference_array(
                        category,
                        object_name,
                        field_rule,
                        value,
                        registry,
                        collector,
                        ep_version,
                    )
                else:
                    _validate_reference_scalar(
                        category,
                        object_name,
                        field_rule,
                        value,
                        registry,
                        collector,
                        ep_version,
                    )


def _build_namespace_registry(
    data: dict[str, Any],
    reference_index: ReferenceIndex,
    collector: IssueCollector,
    ep_version: str | None,
) -> dict[str, dict[str, tuple[str, str]]]:
    registry: dict[str, dict[str, tuple[str, str]]] = {}
    for category, raw_objects in data.items():
        if category == "Version" or not isinstance(raw_objects, dict):
            continue
        namespaces = reference_index.namespaces_by_category.get(category, ())
        provider_fields = reference_index.provider_fields_by_category.get(category, {})
        if not namespaces:
            namespaces = ()
        if not namespaces and not provider_fields:
            continue
        for object_name, obj in raw_objects.items():
            if not isinstance(obj, dict):
                continue
            normalized_object_name = _normalize_name(object_name)
            for namespace in namespaces:
                namespace_bucket = registry.setdefault(namespace, {})
                existing = namespace_bucket.get(normalized_object_name)
                if existing is None:
                    namespace_bucket[normalized_object_name] = (category, object_name)
                    continue
                existing_category, existing_name = existing
                if existing_category == category and existing_name == object_name:
                    continue
                collector.add(
                    "REFERENCE_ERROR",
                    "reference",
                    "error",
                    (
                        f"Object name '{object_name}' conflicts with '{existing_name}' in reference namespace "
                        f"'{namespace}' across categories '{existing_category}' and '{category}'."
                    ),
                    path=f"{category}.{object_name}",
                    category=category,
                    object_name=object_name,
                    details={
                        "namespace": namespace,
                        "existing_category": existing_category,
                        "existing_name": existing_name,
                    },
                    ep_version=ep_version,
                )
            for field_rule in provider_fields.values():
                _register_provider_field(
                    category,
                    object_name,
                    obj,
                    field_rule,
                    registry,
                    collector,
                    ep_version,
                )
    return registry


def _validate_reference_scalar(
    category: str,
    object_name: str,
    field_rule: ReferenceFieldRule,
    value: Any,
    registry: dict[str, dict[str, tuple[str, str]]],
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    if not isinstance(value, str) or not value:
        return
    if _value_exists(registry, field_rule.target_namespaces, value):
        return
    collector.add(
        "REFERENCE_ERROR",
        "reference",
        "error",
        (
            f"Reference '{field_rule.field_name}' points to missing object '{value}' "
            f"in namespaces {', '.join(field_rule.target_namespaces)}."
        ),
        path=f"{category}.{object_name}.{field_rule.field_name}",
        category=category,
        object_name=object_name,
        details={"target_namespaces": list(field_rule.target_namespaces), "target_name": value},
        ep_version=ep_version,
    )


def _validate_reference_array(
    category: str,
    object_name: str,
    field_rule: ReferenceFieldRule,
    values: list[Any],
    registry: dict[str, dict[str, tuple[str, str]]],
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value:
            continue
        if _value_exists(registry, field_rule.target_namespaces, value):
            continue
        collector.add(
            "REFERENCE_ERROR",
            "reference",
            "error",
            (
                f"Reference list '{field_rule.field_name}' contains missing object '{value}' "
                f"in namespaces {', '.join(field_rule.target_namespaces)}."
            ),
            path=f"{category}.{object_name}.{field_rule.field_name}[{index}]",
            category=category,
            object_name=object_name,
            details={"target_namespaces": list(field_rule.target_namespaces), "target_name": value},
            ep_version=ep_version,
        )


def _value_exists(
    registry: dict[str, dict[str, tuple[str, str]]],
    namespaces: tuple[str, ...],
    value: str,
) -> bool:
    normalized_value = _normalize_name(value)
    return any(normalized_value in registry.get(namespace, {}) for namespace in namespaces)


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


def _should_skip_reference_validation(
    category: str,
    field_name: str,
    obj: dict[str, Any],
    data: dict[str, Any],
) -> bool:
    if category == "AirflowNetwork:MultiZone:Surface" and field_name == "external_node_name":
        return _airflow_external_node_reference_is_unused(data)
    if category == "Refrigeration:Case" and field_name == "defrost_energy_correction_curve_name":
        return _refrigeration_defrost_curve_is_unused(obj)
    return False


def _airflow_external_node_reference_is_unused(data: dict[str, Any]) -> bool:
    controls = data.get("AirflowNetwork:SimulationControl")
    if not isinstance(controls, dict):
        return False
    found_control = False
    for control in controls.values():
        if not isinstance(control, dict):
            continue
        found_control = True
        raw_value = control.get("wind_pressure_coefficient_type", "SurfaceAverageCalculation")
        if isinstance(raw_value, str) and raw_value.strip().casefold() == "input":
            return False
    return found_control


def _refrigeration_defrost_curve_is_unused(obj: dict[str, Any]) -> bool:
    defrost_type = obj.get("case_defrost_type")
    curve_type = obj.get("defrost_energy_correction_curve_type")
    if not isinstance(defrost_type, str):
        return True
    normalized_defrost_type = defrost_type.strip().casefold()
    termination_types = {
        "electricwithtemperaturetermination",
        "hotfluidwithtemperaturetermination",
        "hotgaswithtemperaturetermination",
    }
    if normalized_defrost_type not in termination_types:
        return True
    if not isinstance(curve_type, str):
        return False
    normalized_curve_type = curve_type.strip().casefold()
    return normalized_curve_type in {"", "none"}


def _register_provider_field(
    category: str,
    object_name: str,
    obj: dict[str, Any],
    field_rule: ReferenceFieldRule,
    registry: dict[str, dict[str, tuple[str, str]]],
    collector: IssueCollector,
    ep_version: str | None,
) -> None:
    value = obj.get(field_rule.field_name)
    if not isinstance(value, str) or not value:
        return
    normalized_value = _normalize_name(value)
    for namespace in field_rule.target_namespaces:
        namespace_bucket = registry.setdefault(namespace, {})
        existing = namespace_bucket.get(normalized_value)
        if existing is None:
            namespace_bucket[normalized_value] = (category, object_name)
            continue
        existing_category, existing_name = existing
        if existing_category == category and existing_name == object_name:
            continue
        collector.add(
            "REFERENCE_ERROR",
            "reference",
            "error",
            (
                f"Provider value '{value}' from field '{field_rule.field_name}' conflicts with '{existing_name}' "
                f"in reference namespace '{namespace}' across categories '{existing_category}' and '{category}'."
            ),
            path=f"{category}.{object_name}.{field_rule.field_name}",
            category=category,
            object_name=object_name,
            details={
                "namespace": namespace,
                "existing_category": existing_category,
                "existing_name": existing_name,
            },
            ep_version=ep_version,
        )
