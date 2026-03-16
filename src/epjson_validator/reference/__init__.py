"""Reference validation package."""

from epjson_validator.reference.index_builder import build_reference_index
from epjson_validator.reference.validator import validate_references

__all__ = ["build_reference_index", "validate_references"]
