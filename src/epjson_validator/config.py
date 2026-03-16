"""Project configuration and validation constants."""

from __future__ import annotations

DEFAULT_STAGE = "geometry"
VALID_STAGES = ("schema", "reference", "geometry")

STAGE_ORDER = {
    "schema": 1,
    "reference": 2,
    "geometry": 3,
}

SCHEMA_PATH_ENVVAR = "EPJSON_VALIDATOR_SCHEMA_PATH"

PLANAR_TOLERANCE = 1e-5
DISTINCT_TOLERANCE = 1e-7
ZERO_AREA_TOLERANCE = 1e-8
