"""Schema provider loader."""

from __future__ import annotations

from epjson_validator.models import VersionSchema
from epjson_validator.schema.providers.v24_2_0 import SUPPORTED_EP_VERSIONS as V24_2_X_VERSIONS
from epjson_validator.schema.providers.v24_2_0 import get_schema as get_v24_2_0_schema

_PROVIDER_MAP = {
    version: get_v24_2_0_schema
    for version in V24_2_X_VERSIONS
}


def load_version_schema(ep_version: str | None) -> VersionSchema | None:
    if ep_version is None:
        return None
    provider = _PROVIDER_MAP.get(ep_version)
    if provider is None:
        return None
    return provider(ep_version=ep_version)
