"""Audio processing kept inside staging; never writes into Dropbox."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class AudioProcessingError(RuntimeError):
    pass


def overlay_tag(promo: Path, tag: Path, output: Path, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe",
                overlap_seconds: int = 10) -> None:
    """Port legacy station-tag behavior: mix tag into final promo seconds."""
    if not tag.is_file():
        raise AudioProcessingError("tag asset missing")
    if shutil.which(ffmpeg) is None or shutil.which(ffprobe) is None:
        raise AudioProcessingError("ffmpeg or ffprobe unavailable")
    try:
        probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(promo)],
                               check=True, capture_output=True, text=True, timeout=30)
        duration = float(json.loads(probe.stdout)["format"]["duration"])
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError) as error:
        raise AudioProcessingError("cannot determine promo duration") from error
    if duration <= overlap_seconds:
        raise AudioProcessingError("promo shorter than tag overlap")
    start = duration - overlap_seconds
    filter_graph = (
        f"[0:a]atrim=0:{start},asetpts=PTS-STARTPTS[pre];"
        f"[0:a]atrim=start={start},asetpts=PTS-STARTPTS[last];"
        f"[last][1:a]amix=inputs=2:duration=first:normalize=0[mix];"
        f"[pre][mix]concat=n=2:v=0:a=1[out]"
    )
    command = [ffmpeg, "-y", "-i", str(promo), "-i", str(tag), "-filter_complex", filter_graph,
               "-map", "[out]", "-codec:a", "libmp3lame", "-q:a", "2", str(output)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        raise AudioProcessingError("FFmpeg tag overlay failed") from error
    if not output.is_file() or output.stat().st_size == 0:
        raise AudioProcessingError("FFmpeg did not create promo")
