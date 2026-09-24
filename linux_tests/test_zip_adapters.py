import importlib
import zipfile
from pathlib import Path

adapters = importlib.import_module("audio_downloader.sources.adapters")
models = importlib.import_module("audio_downloader.models")
WhittlerDownloader = adapters.WhittlerDownloader
NorthwestOutdoorsDownloader = adapters.NorthwestOutdoorsDownloader
FileContract, Outcome = models.FileContract, models.Outcome


def zip_file(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def test_whittler_maps_provider_parts_to_stable_carts(tmp_path, monkeypatch) -> None:
    archive = zip_file(tmp_path / "provider.zip", {
        "Provider Part A.mp3": b"a", "Provider-Part-B.mp3": b"b",
        "Part_C.mp3": b"c", "show pt D.mp3": b"d",
    })
    downloader = WhittlerDownloader("https://example.test/whittler.zip")
    monkeypatch.setattr(downloader, "_download", lambda staging, name: archive)
    result = downloader.fetch(tmp_path / "staging")
    assert result.outcome == Outcome.SUCCESS
    assert [artifact.contract.filename for artifact in result.artifacts] == [
        "Whittler1.mp3", "Whittler2.mp3", "Whittler3.mp3", "Whittler4.mp3",
    ]
    assert [artifact.path.read_bytes() for artifact in result.artifacts] == [b"a", b"b", b"c", b"d"]


def test_whittler_rejects_incomplete_zip(tmp_path, monkeypatch) -> None:
    archive = zip_file(tmp_path / "provider.zip", {"Part A.mp3": b"a"})
    downloader = WhittlerDownloader("https://example.test/whittler.zip")
    monkeypatch.setattr(downloader, "_download", lambda staging, name: archive)
    assert downloader.fetch(tmp_path / "staging").outcome == Outcome.FAILED


def test_northwest_selects_stable_members_and_ignores_dated_program(tmp_path, monkeypatch) -> None:
    archive = zip_file(tmp_path / "provider.zip", {
        **{f"NWoutdoors{number}.mp3": bytes([number]) for number in range(1, 6)},
        "NWoutdoors_promo.mp3": b"promo", "NWoutdoors092626.mp3": b"dated-program",
    })
    tag = tmp_path / "tag.wav"
    tag.write_bytes(b"tag")
    downloader = NorthwestOutdoorsDownloader("https://example.test/nwo.zip", tag)
    monkeypatch.setattr(downloader, "_download", lambda staging, name: archive)
    monkeypatch.setattr(adapters, "overlay_tag", lambda source, tag, target, *_: target.write_bytes(source.read_bytes() + b"-tagged"))
    result = downloader.fetch(tmp_path / "staging")
    assert result.outcome == Outcome.SUCCESS
    assert [artifact.contract.filename for artifact in result.artifacts] == [
        "NWoutdoors1.mp3", "NWoutdoors2.mp3", "NWoutdoors3.mp3", "NWoutdoors4.mp3", "NWoutdoors5.mp3", "NWoutdoors_promo.mp3",
    ]
    assert (tmp_path / "staging" / "NWoutdoors_promo.mp3").read_bytes() == b"promo-tagged"
    assert not (tmp_path / "staging" / "NWoutdoors092626.mp3").exists()


def test_northwest_rejects_incomplete_archive(tmp_path, monkeypatch) -> None:
    archive = zip_file(tmp_path / "provider.zip", {"NWoutdoors1.mp3": b"one"})
    downloader = NorthwestOutdoorsDownloader("https://example.test/nwo.zip", tmp_path / "tag.wav")
    monkeypatch.setattr(downloader, "_download", lambda staging, name: archive)
    assert downloader.fetch(tmp_path / "staging").outcome == Outcome.FAILED
