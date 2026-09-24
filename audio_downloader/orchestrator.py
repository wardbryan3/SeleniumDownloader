"""Retry policy. Keeps successful sources isolated from failed sources."""
from __future__ import annotations

import time
from collections.abc import Callable, Iterable

from .models import Outcome, SourceResult
from .runner import RETRY_DELAYS_MINUTES, Runner
from .sources.adapters import SourceDownloader


class WeeklyOrchestrator:
    """Run each source once, then retry only unresolved sources."""

    def __init__(self, runner: Runner, sleep: Callable[[float], None] = time.sleep) -> None:
        self.runner = runner
        self.sleep = sleep

    def run(self, downloaders: Iterable[SourceDownloader], command: str = "weekly-run") -> list[SourceResult]:
        pending = list(downloaders)
        latest: dict[str, SourceResult] = {}
        for delay in (None, *RETRY_DELAYS_MINUTES):
            if delay is not None:
                self.sleep(delay * 60)
            results = self.runner.run_many(pending, command)
            latest.update({result.source: result for result in results})
            pending = [downloader for downloader in pending if latest[downloader.name].outcome
                       in {Outcome.FAILED, Outcome.STALE}]
            if not pending:
                break
        return list(latest.values())
