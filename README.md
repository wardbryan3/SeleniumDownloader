# Audio Downloader

Python desktop app that uses Selenium (Firefox) to download radio show audio from 5 sources.

## Quick Start

**Windows users:** Download `AudioDownloader.exe` directly from [GitHub Releases](https://github.com/wardbryan3/SeleniumDownloader/releases) — no Python or dependencies needed.

**From source:**
```bash
git clone ...
cd SeleniumDownloader
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt

# Run GUI (default)
.venv/bin/python3 main.py

# CLI: all sources
.venv/bin/python3 main.py --download-all

# CLI: single source
.venv/bin/python3 main.py --source "Melinda Myers"
```

## Prerequisites

- **Python 3.11+**
- **Firefox** (GeckoDriver auto-installed via webdriver-manager)
- **FFmpeg** (system package, required for audio tag overlay):
  - Linux: `apt install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html

## Configuration

On first run, `download_config.json` is auto-created with defaults (test mode on).

**Required fields to update:**
- `email` / `password` — Westwood One login
- `cow_password` — Clear Out West password
- `urls` — Replace `YOUR_LINK_HERE` placeholders with real URLs
- `test_mode` — Set to `False` for production (uses real Dropbox paths)

## Testing

```bash
.venv/bin/python3 run_all_tests.py
```

All tests are plain Python scripts (no framework). See `AGENTS.md` for developer details.

## Building

```bash
# Local build (Windows only)
pyinstaller --clean AudioDownloader.spec
# Output: dist/AudioDownloader.exe
```

CI automatically builds on push to `main` and creates a GitHub Release on tags.

## Release

1. Bump `__version__` in `__init__.py` (semver: `1.1.9`)
2. `git commit -m "chore: bump version to X.Y.Z"`
3. `git tag X.Y.Z && git push origin main --tags`

The app checks `wardbryan3/SeleniumDownloader/releases/latest` and notifies users of updates.
