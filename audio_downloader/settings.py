"""Linux-only typed settings. Deployment reads one protected env file."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path("/etc/audio-downloader/audio-downloader.env")


class SourceContractSettings(BaseModel):
    """Saved provider filename contract. Values come from live probes."""

    filename: str
    destination: Literal["GLOBAL FEATURES", "Promos", "NBC"] = "GLOBAL FEATURES"
    minimum_bytes: int = Field(default=1, ge=1)
    minimum_duration: float = Field(default=0, ge=0)


class SourceSettings(BaseModel):
    """One source endpoint and output safeguards."""

    transport: Literal["http", "zip", "ftp", "ftps", "session", "api"]
    url: str | None = None
    urls: tuple[str, ...] = ()
    host: str | None = None
    username: str | None = None
    password: SecretStr | None = None
    contracts: tuple[SourceContractSettings, ...] = ()

    @model_validator(mode="after")
    def validate_endpoint(self) -> SourceSettings:
        if self.transport in {"ftp", "ftps"} and not self.host:
            raise ValueError("FTP source requires host")
        if self.transport not in {"ftp", "ftps"} and not (self.url or self.urls):
            raise ValueError("source requires url or urls")
        return self


class Settings(BaseSettings):
    """Validated runtime configuration; never log this object."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", env_prefix="AUDIO_", extra="ignore"
    )
    staging_root: Path = Path("/var/lib/audio-downloader/staging")
    output_root: Path = Path("/var/lib/audio-downloader/dropbox")
    state_db: Path = Path("/var/lib/audio-downloader/state.db")
    dropbox_health_command: str = "pgrep -u audio-downloader dropbox"
    ffprobe_command: str = "ffprobe"
    ffmpeg_command: str = "ffmpeg"
    tag_file: Path | None = None
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    alert_from: str | None = None
    alert_to: str | None = None
    nbc_url: str | None = None
    nbc_affiliate: str = "News-247"
    nbc_api_key: SecretStr | None = None
    timezone: str = "America/Los_Angeles"
    source_names: tuple[str, ...] = (
        "melinda_myers", "northwest_outdoors", "whittler", "weekend_in_the_country",
        "clear_out_west", "aginfo", "rodeoshow",
    )
    source_definitions: dict[str, SourceSettings] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_smtp_pair(self) -> Settings:
        fields = (self.smtp_host, self.smtp_username, self.smtp_password, self.alert_from, self.alert_to)
        if any(value is not None for value in fields) and not all(fields):
            raise ValueError("SMTP configuration requires host, username, password, alert_from, alert_to")
        return self

    def destination(self, station_folder: Literal["GLOBAL FEATURES", "Promos", "NBC"]) -> Path:
        return self.output_root / station_folder

    def missing_for(self, command: str) -> list[str]:
        """Return field names only. Safe for operators and logs."""
        required: list[str] = []
        if command == "nbc-poll":
            if not self.nbc_url:
                required.append("nbc_url")
            if not self.nbc_api_key:
                required.append("nbc_api_key")
        return required


def load_settings(**overrides: Any) -> Settings:
    """Load production env file, or inject values in tests."""
    return Settings(**overrides)
