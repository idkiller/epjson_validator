"""Common type aliases."""

from __future__ import annotations

from typing import Any, Literal

DiagnosticSeverity = Literal["error", "warning", "info", "unsupported"]
ValidationStage = Literal["schema", "reference", "geometry"]
JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None
