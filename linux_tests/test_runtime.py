import importlib
from pathlib import Path
from typing import Any

models = importlib.import_module("audio_downloader.models")
publish_module = importlib.import_module("audio_downloader.publish")
settings_module = importlib.import_module("audio_downloader.settings")
state_module = importlib.import_module("audio_downloader.state")
Artifact, FileContract = models.Artifact, models.FileContract
ValidationError, publish, validate = (publish_module.ValidationError, publish_module.publish, publish_module.validate)
Settings, StateStore = settings_module.Settings, state_module.StateStore


def settings(tmp_path: Path) -> Any:
    return Settings(staging_root=tmp_path / "staging", output_root=tmp_path / "output",
                    state_db=tmp_path / "state.db", dropbox_health_command="true")


def test_migrations_are_idempotent(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.migrate()
    store.migrate()
    run_id = store.start_run("test", "weekly-run")
    store.finish_run(run_id, "success")
    assert store.latest_runs()[0]["outcome"] == "success"


def test_recent_outcomes_are_newest_first(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.migrate()
    for outcome in ("idle", "failed", "failed"):
        run_id = store.start_run("nbc", "nbc-poll")
        store.finish_run(run_id, outcome)
    assert store.recent_outcomes("nbc", 2) == ["failed", "failed"]


def test_validation_then_atomic_publish(tmp_path: Path, monkeypatch) -> None:
    config = settings(tmp_path)
    staged = tmp_path / "CART.mp3"
    staged.write_bytes(b"audio")
    artifact = Artifact(staged, FileContract("CART.mp3", minimum_bytes=5, minimum_duration=1))
    monkeypatch.setattr("audio_downloader.publish.probe_duration", lambda *_: 30.0)
    validate(artifact, config)
    destination = publish(artifact, config)
    assert destination.read_bytes() == b"audio"
    assert artifact.sha256


def test_failed_validation_never_replaces_existing_cart(tmp_path: Path) -> None:
    config = settings(tmp_path)
    target = config.destination("GLOBAL FEATURES") / "CART.mp3"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"old")
    bad = tmp_path / "bad.mp3"
    bad.write_bytes(b"")
    artifact = Artifact(bad, FileContract("CART.mp3"))
    try:
        validate(artifact, config)
    except ValidationError:
        pass
    else:
        raise AssertionError("expected validation failure")
    assert target.read_bytes() == b"old"
