"""Convert a raw EnergyPlus schema into the internal schema model."""

from __future__ import annotations

from typing import Any

from epjson_validator.models import VersionSchema
from epjson_validator.schema.converter.enrich import enrich_raw_schema


def convert_raw_schema(raw_schema: dict[str, Any]) -> VersionSchema:
    enriched = enrich_raw_schema(raw_schema)
    raise NotImplementedError(
        "Raw EnergyPlus schema conversion is scaffolded but not implemented in this MVP. "
        f"Received keys: {sorted(enriched)[:5]}"
    )
