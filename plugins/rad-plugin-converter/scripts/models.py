from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            result["line"] = self.line
        return result


@dataclass(slots=True)
class AuditReport:
    root: Path
    source_types: tuple[str, ...]
    findings: list[Finding] = field(default_factory=list)
    plugin_name: str | None = None

    @property
    def error_count(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    @property
    def info_count(self) -> int:
        return sum(item.severity == "info" for item in self.findings)

    @property
    def conforming(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "source_types": list(self.source_types),
            "plugin_name": self.plugin_name,
            "conforming": self.conforming,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "findings": [item.to_dict() for item in self.findings],
        }


@dataclass(slots=True)
class ConversionResult:
    root: Path
    changed_files: list[str] = field(default_factory=list)
    dry_run: bool = False
    findings: list[Finding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def successful(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "successful": self.successful,
            "dry_run": self.dry_run,
            "error_count": self.error_count,
            "changed_files": self.changed_files,
            "findings": [item.to_dict() for item in self.findings],
        }
