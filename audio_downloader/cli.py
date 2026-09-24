"""Command-line interface for Linux orchestration."""
from __future__ import annotations

import argparse
import fcntl
import importlib
import json
from collections.abc import Sequence

models = importlib.import_module("audio_downloader.models")
runner_module = importlib.import_module("audio_downloader.runner")
settings_module = importlib.import_module("audio_downloader.settings")
state_module = importlib.import_module("audio_downloader.state")
notify_module = importlib.import_module("audio_downloader.notify")
nbc_module = importlib.import_module("audio_downloader.sources.nbc")
orchestrator_module = importlib.import_module("audio_downloader.orchestrator")
registry_module = importlib.import_module("audio_downloader.registry")
Outcome, SourceResult = models.Outcome, models.SourceResult
Runner, load_settings = runner_module.Runner, settings_module.load_settings
StateStore, NBCDownloader = state_module.StateStore, nbc_module.NBCDownloader
Notifier, notify_batch, notify_nbc_transition = notify_module.Notifier, notify_module.notify_batch, notify_module.notify_nbc_transition
WeeklyOrchestrator = orchestrator_module.WeeklyOrchestrator
build_weekly_downloaders = registry_module.build_weekly_downloaders
DAILY_FEATURE_SOURCES = frozenset({"aginfo", "rodeoshow"})


def as_dict(result):
    return {"source": result.source, "outcome": result.outcome, "message": result.message,
            "remote_id": result.remote_id, "artifacts": [item.contract.filename for item in result.artifacts]}


def nbc_poll(settings, state):
    lock_path = settings.state_db.with_suffix(".nbc.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return SourceResult("nbc", Outcome.SKIPPED, message="overlapping poll")
        key = settings.nbc_api_key.get_secret_value() if settings.nbc_api_key else None
        return Runner(settings, state).run_source(
            NBCDownloader(settings.nbc_url, key, settings.nbc_affiliate), "nbc-poll"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m audio_downloader")
    parser.add_argument("--json", action="store_true", dest="as_json")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("weekly-run", "nightly-retry", "aginfo-run", "nbc-poll", "report"):
        commands.add_parser(name)
    probe = commands.add_parser("probe-source")
    probe.add_argument("name")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    missing = settings.missing_for(args.command)
    if missing:
        print(json.dumps({"outcome": "failed", "missing_fields": missing}) if args.as_json else
              "Missing configuration: " + ", ".join(missing))
        return 2
    state = StateStore(settings.state_db)
    state.migrate()
    if args.command == "report":
        report = state.latest_runs()
        print(json.dumps(report, indent=2) if args.as_json else "\n".join(
            f"{row['source']}: {row['outcome']} ({row['message'] or ''})" for row in report))
        return 0
    notifier = Notifier(settings)
    if args.command == "nbc-poll":
        results = [nbc_poll(settings, state)]
        notify_nbc_transition(notifier, results[0], state.recent_outcomes("nbc", 3))
    else:
        downloaders = build_weekly_downloaders(settings)
        if args.command == "probe-source":
            downloaders = [downloader for downloader in downloaders if downloader.name == args.name]
            if not downloaders:
                print(json.dumps({"outcome": "failed", "message": "unknown source"}) if args.as_json else "Unknown source")
                return 2
        if args.command == "aginfo-run":
            downloaders = [downloader for downloader in downloaders if downloader.name in DAILY_FEATURE_SOURCES]
        if args.command == "nightly-retry":
            terminal = {Outcome.SUCCESS, Outcome.IDLE, Outcome.SKIPPED}
            outcomes = state.latest_outcomes()
            downloaders = [downloader for downloader in downloaders if outcomes.get(downloader.name) not in terminal]
        results = WeeklyOrchestrator(Runner(settings, state)).run(downloaders, args.command)
        notify_batch(notifier, args.command, results)
    if args.as_json:
        print(json.dumps([as_dict(result) for result in results]))
    else:
        for result in results:
            print(f"{result.source}: {result.outcome} {result.message or ''}")
    return 0 if all(result.ok for result in results) else 1
