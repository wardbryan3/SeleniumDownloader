import importlib
from datetime import date

adapters = importlib.import_module("audio_downloader.sources.adapters")
MelindaMyersDownloader = adapters.MelindaMyersDownloader
WeekendInTheCountryDownloader = adapters.WeekendInTheCountryDownloader


def test_melinda_maps_verified_mmddyy_filenames() -> None:
    files = [
        "3x/100526_Frost_and_Freeze_Watches.mp3", "5x/100626_Saving_Seeds.mp3",
        "3x/100726_Planting_Tulips.mp3", "5x/100826_Mow_a_Lawn_Maze.mp3", "3x/100926_Extend_Pumpkins.mp3",
    ]
    assert MelindaMyersDownloader.map_coming_week(files, date(2026, 10, 4)) == {
        "MMMON.mp3": files[0], "MMTUE.mp3": files[1], "MMWED.mp3": files[2],
        "MMTHU.mp3": files[3], "MMFRI.mp3": files[4],
    }


def test_witc_chooses_nearest_saturday_promo_only() -> None:
    filenames = ["WITC Promo 07-11-26.mp3", "WITC Promo 2026-07-18.mp3", "WITC Promo 2026-07-04.mp3"]
    assert WeekendInTheCountryDownloader.select_upcoming_saturday_promo(filenames, date(2026, 7, 7)) == "WITC Promo 07-11-26.mp3"
