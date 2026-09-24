"""SQLite state with ordered transactional in-app migrations."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

MIGRATION_COUNT = 2


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    version: Mapped[int] = mapped_column(Integer, primary_key=True)


class SourceRun(Base):
    __tablename__ = "source_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String, index=True)
    command: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String)
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    remote_id: Mapped[str | None] = mapped_column(String, nullable=True)
    remote_date: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[str] = mapped_column(String)
    finished_at: Mapped[str | None] = mapped_column(String, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)


class StoredArtifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("source_runs.id"))
    filename: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    expected: Mapped[bool] = mapped_column(Boolean)
    sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation: Mapped[str] = mapped_column(String)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[str] = mapped_column(String)


class HealthObservation(Base):
    __tablename__ = "health_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checked_at: Mapped[str] = mapped_column(String)
    healthy: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[str] = mapped_column(String)


def now() -> str:
    return datetime.now(UTC).isoformat()


class StateStore:
    def __init__(self, database: Path) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{database}", future=True)

    def migrate(self) -> None:
        """Create schema then record every fixed migration transactionally."""
        with Session(self.engine) as session, session.begin():
            Base.metadata.create_all(self.engine)
            applied = set(session.scalars(select(SchemaVersion.version)))
            for version in range(1, MIGRATION_COUNT + 1):
                if version not in applied:
                    session.add(SchemaVersion(version=version))

    def start_run(self, source: str, command: str, remote_id: str | None = None) -> int:
        with Session(self.engine) as session, session.begin():
            run = SourceRun(source=source, command=command, outcome="failed", remote_id=remote_id,
                            started_at=now(), fallback_used=False)
            session.add(run)
            session.flush()
            if run.id is None:
                raise RuntimeError("database did not return run id")
            return run.id

    def finish_run(self, run_id: int, outcome: str, message: str | None = None, fallback_used: bool = False) -> None:
        with Session(self.engine) as session, session.begin():
            run = session.get(SourceRun, run_id)
            if run is None:
                raise ValueError("unknown run")
            run.outcome, run.message, run.fallback_used, run.finished_at = outcome, message, fallback_used, now()

    def record_artifact(self, run_id: int, *, filename: str, destination: str, expected: bool,
                        sha256: str | None, size_bytes: int | None, duration_seconds: float | None,
                        validation: str, published: bool, stale: bool = False) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(StoredArtifact(run_id=run_id, filename=filename, destination=destination, expected=expected,
                sha256=sha256, size_bytes=size_bytes, duration_seconds=duration_seconds, validation=validation,
                published=published, stale=stale, first_seen_at=now()))

    def record_health(self, healthy: bool, detail: str) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(HealthObservation(checked_at=now(), healthy=healthy, detail=detail))

    def latest_runs(self) -> list[dict[str, object]]:
        with Session(self.engine) as session:
            return [{"source": run.source, "command": run.command, "outcome": run.outcome,
                     "message": run.message, "remote_id": run.remote_id, "started_at": run.started_at,
                     "finished_at": run.finished_at} for run in session.scalars(select(SourceRun).order_by(SourceRun.id.desc()))]

    def latest_outcomes(self) -> dict[str, str]:
        """Latest terminal outcome per source, used to avoid repeat downloads."""
        outcomes: dict[str, str] = {}
        for run in self.latest_runs():
            outcomes.setdefault(str(run["source"]), str(run["outcome"]))
        return outcomes

    def recent_outcomes(self, source: str, limit: int) -> list[str]:
        """Newest-first terminal outcomes for transition-based alert policy."""
        with Session(self.engine) as session:
            statement = select(SourceRun.outcome).where(SourceRun.source == source).order_by(SourceRun.id.desc()).limit(limit)
            return [str(outcome) for outcome in session.scalars(statement)]
