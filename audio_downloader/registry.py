"""Build adapters only from typed, live-verified source definitions."""
from __future__ import annotations

from pathlib import Path

from .models import FileContract, Outcome, SourceResult
from .settings import Settings, SourceSettings
from .sources.adapters import (
    AgInfoDownloader,
    ClearOutWestDownloader,
    MelindaMyersDownloader,
    NorthwestOutdoorsDownloader,
    RodeoShowDownloader,
    SourceDownloader,
    WeekendInTheCountryDownloader,
    WhittlerDownloader,
)


class UnverifiedDownloader(SourceDownloader):
    def __init__(self, name: str, reason: str) -> None:
        self.name, self.reason = name, reason

    def fetch(self, staging: Path) -> SourceResult:
        return SourceResult(self.name, Outcome.UNVERIFIED, message=self.reason)


def contracts(definition: SourceSettings) -> list[FileContract]:
    return [FileContract(item.filename, item.destination, item.minimum_bytes, item.minimum_duration)
            for item in definition.contracts]


def build_weekly_downloaders(settings: Settings) -> list[SourceDownloader]:
    """Never infer missing provider contracts or silently omit a source."""
    output: list[SourceDownloader] = []
    for name in settings.source_names:
        definition = settings.source_definitions.get(name)
        if definition is None:
            output.append(UnverifiedDownloader(name, "missing source definition"))
            continue
        files = contracts(definition)
        if name == "whittler" and definition.transport == "zip":
            output.append(WhittlerDownloader(definition.url))
        elif name == "northwest_outdoors" and definition.transport == "zip":
            output.append(NorthwestOutdoorsDownloader(definition.url, settings.tag_file,
                                                       settings.ffmpeg_command, settings.ffprobe_command))
        elif name == "melinda_myers" and definition.transport == "ftps":
            password = definition.password.get_secret_value() if definition.password else None
            output.append(MelindaMyersDownloader(definition.host, definition.username, password) if password
                          else UnverifiedDownloader(name, "Melinda FTPS credentials missing"))
        elif name == "weekend_in_the_country" and definition.transport == "ftp":
            password = definition.password.get_secret_value() if definition.password else None
            output.append(WeekendInTheCountryDownloader(definition.host, definition.username, password, files))
        elif name == "clear_out_west" and definition.transport == "session" and files:
            password = definition.password.get_secret_value() if definition.password else None
            output.append(ClearOutWestDownloader(definition.url, password, files))
        elif name == "aginfo" and definition.transport == "http" and len(definition.urls) == 3:
            output.append(AgInfoDownloader(definition.urls))
        elif name == "rodeoshow" and definition.transport == "http" and len(files) == 1:
            output.append(RodeoShowDownloader(definition.url, files[0]))
        else:
            output.append(UnverifiedDownloader(name, "unsupported or incomplete source contract"))
    return output
