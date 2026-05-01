# AGENTS.md — SeleniumDownloader

## What This Is

Python desktop app using Selenium (Firefox) to download radio show audio from 5 Dropbox sources.

## Environment

Virtual environment at `.venv/` (gitignored). Use it for all commands:
```bash
.venv/bin/python3 main.py                         # GUI (default)
.venv/bin/python3 main.py --download-all          # CLI: all sources
.venv/bin/python3 main.py --source "Melinda Myers"  # CLI: one source
```

Install dependencies into `.venv/`:
```bash
.venv/bin/python3 -m pip install selenium webdriver-manager psutil watchdog pyinstaller
```

## Commands

```bash
.venv/bin/python3 test_downloads.py                    # Standalone test suite
.venv/bin/python3 test_detection_standalone.py         # Download detection test
.venv/bin/python3 tests/test_config_edge_cases.py      # Config tests
.venv/bin/python3 tests/test_integration.py            # Integration tests
.venv/bin/python3 tests/test_scheduler.py              # Scheduler tests
.venv/bin/python3 tests/test_sources.py                # URL validation tests
.venv/bin/python3 tests/test_browser_manager.py        # Browser manager tests
```

No test framework — tests are plain Python scripts run directly. No lint/typecheck configured.

## Architecture

- **Entry point**: `main.py` — GUI (tkinter), CLI download-all, CLI single-source
- **Sources**: `sources/` — 5 downloaders via factory `create_downloader(name, browser_mgr, config)`
- **Base class**: `sources/base.py` — `BaseDownloader` with `download()` abstract method
- **Browser**: Firefox only (`webdriver-manager` for GeckoDriver auto-install)
- **Config**: `download_config.json` (gitignored, auto-created with defaults)

## Gotchas

- **Test mode defaults `True`** — output goes to `downloads/`, not Dropbox paths
- **Two download dirs**: `browser_downloads/` is Selenium staging; `downloads/` (test) or Dropbox (prod) is final output
- **Source names vs keys**: `DOWNLOAD_SOURCES` maps display names (`"Melinda Myers"`) to module keys (`"melinda_myers"`) — use display names with `create_downloader()`
- **Config merge**: `DEFAULT_CONFIG.copy()` then `.update(saved_config)` — top-level keys only, nested dicts like `urls` are fully replaced
- **Constants use UPPERCASE**: `ALLOWED_EXTENSIONS`, `EXCLUDED_EXTENSIONS`, `EXCLUDED_PREFIXES` in `constants.py`
- **FFmpeg required**: Must be on system PATH for audio tag overlay (`download_utils.py`)
- **Windows-only build**: PyInstaller spec builds `.exe` on Windows CI

## Dependencies

`selenium`, `webdriver-manager`, `psutil`, `watchdog`, `pyinstaller` (+ `ffmpeg` system package)

## Adding Sources

Register in 4 places:
1. `sources/<snake_case_name>.py` — inherit `BaseDownloader`, implement `download(update_callback=None) -> bool`
2. `sources/__init__.py` — import and add to `downloaders` dict in `create_downloader()`
3. `config.py` — add to `DOWNLOAD_SOURCES` dict
4. `AudioDownloader.spec` — add to `hiddenimports` (PyInstaller won't auto-discover dynamic imports)

Verify:
```bash
python -c "from sources import create_downloader; from browser_manager import BrowserManager; from config import ConfigManager; bm = BrowserManager(ConfigManager()); d = create_downloader('Display Name', bm, ConfigManager()); print('OK')"
```

## Release Workflow

1. Bump `__version__` in `__init__.py` (semver: `1.1.9`)
2. `git commit -m "chore: bump version to X.Y.Z"`
3. `git tag X.Y.Z && git push origin main --tags`

CI (`.github/workflows/windows_build.yml`) builds `dist/AudioDownloader.exe` and creates a GitHub Release.

`update_checker.py` compares `__version__` against `wardbryan3/SeleniumDownloader/releases/latest`.

## Local Build

```bash
pyinstaller --clean AudioDownloader.spec
```

Keep `hiddenimports` in sync when adding modules — PyInstaller cannot detect runtime-imported modules.

Executable reads config from its own directory. Does not bundle FFmpeg.
