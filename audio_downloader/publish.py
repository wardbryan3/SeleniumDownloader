"""Validation and atomic Dropbox publication."""
from __future__ import annotations

import hashlib
import json
import shlex
import shutil
import subprocess
from pathlib import Path

from .models import Artifact
from .settings import Settings


class ValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_duration(path: Path, ffprobe: str) -> float:
    command = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    try:
        output = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
        return float(json.loads(output.stdout)["format"]["duration"])
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError) as error:
        raise ValidationError(f"ffprobe unreadable: {error}") from error


def validate(artifact: Artifact, settings: Settings) -> Artifact:
    path = artifact.path
    if path.name != artifact.contract.filename:
        raise ValidationError("wrong output name")
    if not path.is_file() or path.stat().st_size < artifact.contract.minimum_bytes:
        raise ValidationError("zero-byte or under-threshold output")
    artifact.size_bytes = path.stat().st_size
    artifact.duration_seconds = probe_duration(path, settings.ffprobe_command)
    if artifact.duration_seconds < artifact.contract.minimum_duration:
        raise ValidationError("under-duration output")
    artifact.sha256 = sha256_file(path)
    artifact.validation = "validated"
    return artifact


def dropbox_healthy(settings: Settings) -> tuple[bool, str]:
    try:
        result = subprocess.run(shlex.split(settings.dropbox_health_command), check=False,
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as error:
        return False, f"health command failed: {type(error).__name__}"
    return result.returncode == 0, "healthy" if result.returncode == 0 else "Dropbox health command failed"


def publish(artifact: Artifact, settings: Settings) -> Path:
    """Copy then atomically replace only after all caller validations pass."""
    healthy, detail = dropbox_healthy(settings)
    if not healthy:
        raise ValidationError(detail)
    destination = settings.destination(artifact.contract.destination) / artifact.contract.filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.new")
    try:
        shutil.copyfile(artifact.path, temporary)
        # Same-directory replace guarantees same-filesystem atomicity.
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def require_tag_tools(settings: Settings) -> None:
    if settings.tag_file is None or not settings.tag_file.is_file():
        raise ValidationError("tag_file missing")
    if shutil.which(settings.ffmpeg_command) is None:
        raise ValidationError("ffmpeg unavailable")
