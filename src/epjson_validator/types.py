"""Common type aliases."""

from __future__ import annotations

from typing import Any, Literal

DiagnosticSeverity = Literal["error", "warning", "info", "unsupported"]
ValidationStage = Literal["schema", "reference", "geometry", "visualization"]
ProfileName = Literal["svg-plan", "svg-elevation", "three-basic"]
JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None
