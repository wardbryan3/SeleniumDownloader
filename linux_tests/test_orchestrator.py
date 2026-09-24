import importlib

models = importlib.import_module("audio_downloader.models")
orchestrator_module = importlib.import_module("audio_downloader.orchestrator")
Outcome, SourceResult = models.Outcome, models.SourceResult
WeeklyOrchestrator = orchestrator_module.WeeklyOrchestrator


class Downloader:
    def __init__(self, name: str) -> None:
        self.name = name


class Runner:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.attempts: dict[str, int] = {}

    def run_many(self, downloaders, command):
        results = []
        for downloader in downloaders:
            self.calls.append(downloader.name)
            self.attempts[downloader.name] = self.attempts.get(downloader.name, 0) + 1
            outcome = Outcome.SUCCESS if downloader.name == "good" or self.attempts[downloader.name] == 2 else Outcome.FAILED
            results.append(SourceResult(downloader.name, outcome))
        return results


def test_successful_source_is_not_retried() -> None:
    runner = Runner()
    waits: list[float] = []
    results = WeeklyOrchestrator(runner, sleep=waits.append).run([Downloader("good"), Downloader("late")])
    assert runner.calls == ["good", "late", "late"]
    assert waits == [300]
    assert {result.source: result.outcome for result in results} == {"good": Outcome.SUCCESS, "late": Outcome.SUCCESS}
