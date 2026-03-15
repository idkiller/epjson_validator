"""Raw schema enrichment hooks for future schema conversion."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def enrich_raw_schema(raw_schema: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(raw_schema)
