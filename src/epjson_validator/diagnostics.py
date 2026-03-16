"""Structured diagnostics and report models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationIssue:
    code: str
    stage: str
    severity: str
    message: str
    path: str | None = None
    category: str | None = None
    object_name: str | None = None
    details: dict[str, Any] | None = None
    suggestion: str | None = None
    ep_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    ok: bool
    issues: list[ValidationIssue]
    summary: dict[str, Any]
    ep_version: str | None = None
    schema_version: str | None = None
    parametric_expanded: bool = False
    parametric_run: int | None = None
    parametric_available_runs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary,
            "ep_version": self.ep_version,
            "schema_version": self.schema_version,
            "parametric_expanded": self.parametric_expanded,
            "parametric_run": self.parametric_run,
            "parametric_available_runs": self.parametric_available_runs,
        }


@dataclass(slots=True)
class IssueCollector:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(
        self,
        code: str,
        stage: str,
        severity: str,
        message: str,
        *,
        path: str | None = None,
        category: str | None = None,
        object_name: str | None = None,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
        ep_version: str | None = None,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                code=code,
                stage=stage,
                severity=severity,
                message=message,
                path=path,
                category=category,
                object_name=object_name,
                details=details,
                suggestion=suggestion,
                ep_version=ep_version,
            )
        )

    def extend(self, issues: list[ValidationIssue]) -> None:
        self.issues.extend(issues)


def build_summary(issues: list[ValidationIssue]) -> dict[str, Any]:
    counts_by_stage: dict[str, int] = {}
    summary = {
        "error_count": 0,
        "warning_count": 0,
        "info_count": 0,
        "unsupported_count": 0,
        "counts_by_stage": counts_by_stage,
    }
    for issue in issues:
        counts_by_stage[issue.stage] = counts_by_stage.get(issue.stage, 0) + 1
        if issue.severity == "error":
            summary["error_count"] += 1
        elif issue.severity == "warning":
            summary["warning_count"] += 1
        elif issue.severity == "info":
            summary["info_count"] += 1
        elif issue.severity == "unsupported":
            summary["unsupported_count"] += 1
    return summary
