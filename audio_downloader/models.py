"""Runtime result and output contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal


class Outcome(StrEnum):
    SUCCESS = "success"
    STALE = "stale"
    FAILED = "failed"
    UNVERIFIED = "unverified"
    IDLE = "idle"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class FileContract:
    filename: str
    destination: Literal["GLOBAL FEATURES", "Promos", "NBC"] = "GLOBAL FEATURES"
    minimum_bytes: int = 1
    minimum_duration: float = 0.0
    required: bool = True


@dataclass
class Artifact:
    path: Path
    contract: FileContract
    remote_id: str | None = None
    remote_date: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    validation: str | None = None


@dataclass
class SourceResult:
    source: str
    outcome: Outcome
    artifacts: list[Artifact] = field(default_factory=list)
    message: str | None = None
    remote_id: str | None = None
    fallback_used: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome in {Outcome.SUCCESS, Outcome.IDLE, Outcome.SKIPPED}
