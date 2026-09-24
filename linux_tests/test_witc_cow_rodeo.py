import importlib
from contextlib import contextmanager
from datetime import date

adapters = importlib.import_module("audio_downloader.sources.adapters")
models = importlib.import_module("audio_downloader.models")
FileContract, Outcome = models.FileContract, models.Outcome
ClearOutWestDownloader = adapters.ClearOutWestDownloader
RodeoShowDownloader = adapters.RodeoShowDownloader
WeekendInTheCountryDownloader = adapters.WeekendInTheCountryDownloader


class WITCFake(WeekendInTheCountryDownloader):
    @contextmanager
    def insecure_curl(self):
        yield [], "provider.example"

    def list_files(self, common, host, remote_path=""):
        if not remote_path:
            return [self.ROOT_DIRECTORY]
        return [
            *(f"Weekend hr{hour}_seg{segment}.mp3" for hour in range(1, 3) for segment in range(1, 5)),
            "Weekend Promo 2026-07-11.mp3", "Weekend Promo 2026-07-18.mp3",
        ]

    def download_file(self, common, host, remote_path, target):
        target.write_bytes(b"audio")


def test_witc_fetches_eight_segments_and_only_nearest_promo(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(adapters, "datetime", type("Clock", (), {"now": staticmethod(lambda _: type("Now", (), {"date": lambda self: date(2026, 7, 7)})())}))
    result = WITCFake("provider.example", "station", "password", []).fetch(tmp_path)
    assert result.outcome == Outcome.SUCCESS
    assert len(result.artifacts) == 9
    assert result.details == {"insecure_transport": True}
    assert {item.path.name for item in result.artifacts} >= {"Weekend Promo 2026-07-11.mp3"}
    assert not (tmp_path / "Weekend Promo 2026-07-18.mp3").exists()


class Response:
    def __init__(self, text="", body=b"audio", url="https://cow.example/download"):
        self.text, self.body, self.url = text, body, url

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Session:
    def __init__(self):
        self.headers = {}
        self.post_data = None

    def get(self, url, **kwargs):
        if kwargs.get("stream"):
            return Response(url=url)
        return Response('<form action="/login"><input name="redirect" value="/download"><input name="u" value="radio"><input name="p"></form>')

    def post(self, url, data, **kwargs):
        self.post_data = data
        links = "".join(f'<a href="https://files.example/showtrack{number:02}.mp3">track</a>' for number in range(1, 6))
        return Response(links)


COW_FILES = {"COW1.mp3", "COW2.mp3", "COW3.mp3", "COW4.mp3", "COWPROMO.mp3"}


def test_cow_posts_hidden_fields_and_downloads_five_contracted_files(tmp_path, monkeypatch) -> None:
    session = Session()
    monkeypatch.setattr(adapters.requests, "Session", lambda: session)
    contracts = [FileContract(name) for name in sorted(COW_FILES)]
    result = ClearOutWestDownloader("https://cow.example/download", "secret", contracts).fetch(tmp_path)
    assert result.outcome == Outcome.SUCCESS
    assert session.post_data == {"redirect": "/download", "u": "radio", "p": "secret"}
    assert {item.path.name for item in result.artifacts} == COW_FILES


def test_rodeoshow_streams_to_fixed_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(adapters.requests, "get", lambda *args, **kwargs: Response())
    result = RodeoShowDownloader("https://provider.example/rodeo").fetch(tmp_path)
    assert result.outcome == Outcome.SUCCESS
    assert result.artifacts[0].contract.filename == "RODEOSHOW.mp3"
