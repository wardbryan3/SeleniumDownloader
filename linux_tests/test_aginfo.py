import importlib

adapters = importlib.import_module("audio_downloader.sources.adapters")
models = importlib.import_module("audio_downloader.models")
AgInfoDownloader = adapters.AgInfoDownloader
Outcome = models.Outcome


class Response:
    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int):
        yield b"audio"

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_aginfo_streams_three_feeds_without_content_length(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(adapters.requests, "get", lambda *args, **kwargs: Response())
    result = AgInfoDownloader(("https://one", "https://two", "https://three")).fetch(tmp_path)
    assert result.outcome == Outcome.SUCCESS
    assert [artifact.contract.filename for artifact in result.artifacts] == ["AGRIBIZ.mp3", "MARKETAG.mp3", "LOA.mp3"]
    assert all(artifact.path.read_bytes() == b"audio" for artifact in result.artifacts)


def test_aginfo_rejects_incomplete_endpoint_contract(tmp_path) -> None:
    result = AgInfoDownloader(("https://one",)).fetch(tmp_path)
    assert result.outcome == Outcome.UNVERIFIED
