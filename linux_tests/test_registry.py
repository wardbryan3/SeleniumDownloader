import importlib
import os

settings_module = importlib.import_module("audio_downloader.settings")
registry_module = importlib.import_module("audio_downloader.registry")
Settings, SourceSettings = settings_module.Settings, settings_module.SourceSettings
build_weekly_downloaders = registry_module.build_weekly_downloaders


def test_missing_contracts_remain_explicitly_unverified(tmp_path) -> None:
    settings = Settings(staging_root=tmp_path / "staging", output_root=tmp_path / "output", state_db=tmp_path / "state.db")
    downloaders = build_weekly_downloaders(settings)
    results = [downloader.fetch(tmp_path) for downloader in downloaders]
    assert {result.source for result in results} == set(settings.source_names)
    assert {str(result.outcome) for result in results} == {"unverified"}


def test_melinda_uses_verified_ftps_definition(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUDIO_DOWNLOADER_TEST_PASSWORD", "test")
    settings = Settings(staging_root=tmp_path / "staging", output_root=tmp_path / "output", state_db=tmp_path / "state.db",
        source_definitions={"melinda_myers": SourceSettings(transport="ftps", host="provider.example", username="station", password=os.environ["AUDIO_DOWNLOADER_TEST_PASSWORD"])})
    downloader = next(item for item in build_weekly_downloaders(settings) if item.name == "melinda_myers")
    assert downloader.host == "provider.example"


def test_whittler_uses_typed_zip_definition(tmp_path) -> None:
    settings = Settings(staging_root=tmp_path / "staging", output_root=tmp_path / "output", state_db=tmp_path / "state.db",
        source_definitions={"whittler": SourceSettings(transport="zip", url="https://example.test/whittler.zip")})
    downloader = next(item for item in build_weekly_downloaders(settings) if item.name == "whittler")
    assert downloader.url == "https://example.test/whittler.zip"


def test_t12_sources_require_verified_transport_definitions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUDIO_DOWNLOADER_TEST_PASSWORD", "test")
    password = os.environ["AUDIO_DOWNLOADER_TEST_PASSWORD"]
    settings = Settings(staging_root=tmp_path / "staging", output_root=tmp_path / "output", state_db=tmp_path / "state.db",
        source_definitions={
            "weekend_in_the_country": SourceSettings(transport="ftp", host="ftp.example", username="station", password=password),
            "clear_out_west": SourceSettings(transport="session", url="https://cow.example", password=password,
                contracts=tuple({"filename": f"COW{number}.mp3"} for number in range(1, 6))),
            "rodeoshow": SourceSettings(transport="http", url="https://rodeo.example",
                contracts=({"filename": "RODEOSHOW.mp3", "minimum_bytes": 1_000_000},)),
        })
    downloaders = {item.name: item for item in build_weekly_downloaders(settings)}
    assert downloaders["weekend_in_the_country"].host == "ftp.example"
    assert downloaders["clear_out_west"].password == password
    assert downloaders["rodeoshow"].contracts[0].minimum_bytes == 1_000_000
