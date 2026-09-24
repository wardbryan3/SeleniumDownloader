import importlib

models = importlib.import_module("audio_downloader.models")
nbc_module = importlib.import_module("audio_downloader.sources.nbc")
Outcome = models.Outcome
NBCDownloader = nbc_module.NBCDownloader


class Response:
    def __init__(self, text: str = "", body: bytes = b"") -> None:
        self.text, self.body = text, body

    def raise_for_status(self) -> None:
        return None

    def json(self):
        raise ValueError("line manifest")

    def iter_content(self, size: int):
        yield self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_nbc_empty_line_manifest_is_idle(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(nbc_module.requests, "get", lambda *args, **kwargs: Response())
    result = NBCDownloader("https://api.example/audio", "key").fetch(tmp_path)
    assert result.outcome == Outcome.IDLE


def test_nbc_line_manifest_preserves_provider_filename(tmp_path, monkeypatch) -> None:
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/newFiles"):
            return Response("https://files.example/path/News-247-001.mp3?token=temporary\n")
        return Response(body=b"audio")

    monkeypatch.setattr(nbc_module.requests, "get", get)
    result = NBCDownloader("https://api.example/audio", "key").fetch(tmp_path)
    assert result.outcome == Outcome.SUCCESS
    assert result.artifacts[0].contract.filename == "News-247-001.mp3"
    assert (tmp_path / "News-247-001.mp3").read_bytes() == b"audio"
    assert all(call[1]["headers"]["X-API-Key"] == "key" for call in calls)
