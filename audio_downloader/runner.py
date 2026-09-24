"""Source isolation, validation, publish, state transitions, and retry policy."""
from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .models import Outcome, SourceResult
from .publish import ValidationError, dropbox_healthy, publish, validate
from .settings import Settings
from .sources.adapters import SourceDownloader
from .state import StateStore


class Runner:
    def __init__(self, settings: Settings, state: StateStore) -> None:
        self.settings, self.state = settings, state

    def run_source(self, downloader: SourceDownloader, command: str) -> SourceResult:
        self.settings.staging_root.mkdir(parents=True, exist_ok=True)
        run_id = self.state.start_run(downloader.name, command)
        staging = Path(tempfile.mkdtemp(prefix=f"{downloader.name}-", dir=self.settings.staging_root))
        try:
            result = downloader.fetch(staging)
            if result.outcome != Outcome.SUCCESS:
                self.state.finish_run(run_id, result.outcome, result.message, result.fallback_used)
                return result
            healthy, detail = dropbox_healthy(self.settings)
            self.state.record_health(healthy, detail)
            if not healthy:
                raise ValidationError(detail)
            for artifact in result.artifacts:
                validate(artifact, self.settings)
                publish(artifact, self.settings)
                self.state.record_artifact(run_id, filename=artifact.contract.filename,
                    destination=artifact.contract.destination, expected=artifact.contract.required,
                    sha256=artifact.sha256, size_bytes=artifact.size_bytes,
                    duration_seconds=artifact.duration_seconds, validation=artifact.validation or "validated",
                    published=True)
            self.state.finish_run(run_id, Outcome.SUCCESS, result.message, result.fallback_used)
            return result
        except (OSError, ValidationError) as error:
            # Existing destination remains untouched: failure means stale cart, never partial publish.
            result = SourceResult(downloader.name, Outcome.STALE, message=str(error))
            self.state.finish_run(run_id, result.outcome, result.message)
            return result
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def run_many(self, downloaders: Iterable[SourceDownloader], command: str) -> list[SourceResult]:
        return [self.run_source(downloader, command) for downloader in downloaders]


RETRY_DELAYS_MINUTES = (5, 15, 60)
