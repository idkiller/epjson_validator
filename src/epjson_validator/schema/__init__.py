"""Schema support package."""

from epjson_validator.schema.base import validate_against_schema
from epjson_validator.schema.loader import load_version_schema

__all__ = ["load_version_schema", "validate_against_schema"]
