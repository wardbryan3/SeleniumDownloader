"""Direct source adapters. Adapters stage only; runner owns publication."""
from audio_downloader.sources.adapters import (
    AgInfoDownloader,
    ClearOutWestDownloader,
    MelindaMyersDownloader,
    NorthwestOutdoorsDownloader,
    RodeoShowDownloader,
    WeekendInTheCountryDownloader,
    WhittlerDownloader,
)
from audio_downloader.sources.nbc import NBCDownloader

__all__ = [
    "AgInfoDownloader", "ClearOutWestDownloader", "MelindaMyersDownloader",
    "NBCDownloader", "NorthwestOutdoorsDownloader", "RodeoShowDownloader",
    "WeekendInTheCountryDownloader", "WhittlerDownloader",
]
