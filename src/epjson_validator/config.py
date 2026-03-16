"""Project configuration and validation constants."""

from __future__ import annotations

SUPPORTED_EP_VERSIONS = ("24.1.0", "24.2.0")
DEFAULT_PROFILE = "svg-plan"
DEFAULT_STAGE = "visualization"
VALID_STAGES = ("schema", "reference", "geometry", "visualization")
VALID_PROFILES = ("svg-plan", "svg-elevation", "three-basic")

STAGE_ORDER = {
    "schema": 1,
    "reference": 2,
    "geometry": 3,
    "visualization": 4,
}

PLANAR_TOLERANCE = 1e-5
DISTINCT_TOLERANCE = 1e-7
ZERO_AREA_TOLERANCE = 1e-8
