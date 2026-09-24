import importlib

models = importlib.import_module("audio_downloader.models")
notify = importlib.import_module("audio_downloader.notify")
Outcome, SourceResult = models.Outcome, models.SourceResult


class Sink:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, subject: str, body: str) -> None:
        self.messages.append((subject, body))


def test_weekly_failure_and_summary_alerts() -> None:
    sink = Sink()
    notify.notify_batch(sink, "weekly-run", [SourceResult("good", Outcome.SUCCESS), SourceResult("bad", Outcome.STALE)])
    assert sink.messages == [
        ("Audio weekly source failure: bad", "Outcome: stale"),
        ("Audio weekly run summary", "good: success\nbad: stale"),
    ]


def test_nightly_alerts_only_unresolved_sources() -> None:
    sink = Sink()
    notify.notify_batch(sink, "nightly-retry", [SourceResult("bad", Outcome.FAILED), SourceResult("good", Outcome.SUCCESS)])
    assert sink.messages == [("Audio nightly retry failure: bad", "Outcome: failed")]


def test_nbc_alerts_at_second_failure_and_on_recovery() -> None:
    sink = Sink()
    notify.notify_nbc_transition(sink, SourceResult("nbc", Outcome.FAILED), ["failed", "failed", "idle"])
    notify.notify_nbc_transition(sink, SourceResult("nbc", Outcome.FAILED), ["failed", "failed", "failed"])
    notify.notify_nbc_transition(sink, SourceResult("nbc", Outcome.IDLE), ["idle", "failed", "failed"])
    assert sink.messages == [
        ("Audio NBC poll failure", "Two consecutive NBC polls failed."),
        ("Audio NBC poll recovered", "NBC poll outcome: idle"),
    ]


def test_notification_transport_error_does_not_break_download_run() -> None:
    class BrokenSink:
        def send(self, subject: str, body: str) -> None:
            raise OSError("mail offline")

    notify.notify_batch(BrokenSink(), "weekly-run", [SourceResult("bad", Outcome.FAILED)])
