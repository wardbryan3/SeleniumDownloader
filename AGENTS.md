# AGENTS.md — SeleniumDownloader

## What This Is

Audio Download Manager — a Python desktop app that uses Selenium (Firefox) to download radio show audio files from 4 Dropbox sources and organizes them into Dropbox folders.

## Developer Commands

```bash
python -m audio_downloader                  # Launch GUI (default)
python -m audio_downloader --download-all   # CLI: download from all sources
python -m audio_downloader --source "Name"  # CLI: download from one source
python tests/test_downloads.py        # Run standalone test suite
python tests/test_detection_standalone.py  # Run download detection test
python tests/test_config_edge_cases.py  # Config tests
python tests/test_integration.py        # Integration tests
python tests/test_sources.py            # URL validation tests
python tests/test_browser_manager.py    # Browser manager tests
python tests/test_weekend_in_the_country.py  # WITC rename/promo tests
```

No test framework installed — tests are plain Python scripts run directly. No lint/typecheck configured.

## Architecture

- **Entry point**: `audio_downloader/main.py` (run via `python -m audio_downloader`) — 3 modes: GUI (tkinter), CLI download-all, CLI single-source
- **Windows batch scripts**: `scripts/download_global_features.bat` (Thu 11PM), `scripts/download_promos.bat` (Tue 11PM)
- **Sources**: `audio_downloader/sources/` — 6 downloader implementations using factory via `create_downloader(name, browser_mgr, config)`
- **Base class**: `audio_downloader/sources/base.py` — `BaseDownloader` with `download()` abstract method
- **Browser**: Firefox only (uses `webdriver-manager` for GeckoDriver auto-install)
- **Config**: `download_config.json` (gitignored, contains credentials) — auto-created with defaults on first run
- **GUI**: tkinter dark theme in `audio_downloader/gui.py`

## Key Directories

| Directory | Purpose | Gitignored? |
|---|---|---|
| `downloads/` | Test mode output | yes |
| `browser_downloads/` | Selenium staging dir | yes |
| `audio_downloader/` | Application package (sources, config, GUI, etc.) | no |
| `audio_downloader/sources/` | Download source implementations | no |
| `tests/` | Test suite | no |
| `scripts/` | Windows batch scripts | no |

## Important Conventions & Gotchas

- **Test mode defaults to `True`** — downloads go to `downloads/` not real Dropbox paths
- **Two download directories**: `browser_downloads/` is the Selenium staging area; `downloads/` (test) or Dropbox paths (prod) are final output
- **FFmpeg is external** — must be installed on the system separately for audio tag overlay (`audio_downloader/download_utils.py`)
- **Windows-only build**: PyInstaller spec builds `.exe` on Windows CI (`AudioDownloader.spec`)
- **Source names vs keys**: `DOWNLOAD_SOURCES` maps display names (e.g. `"Melinda Myers"`) to module keys (e.g. `"melinda_myers"`) — always use display names with `create_downloader()`
- **Config merge**: `DEFAULT_CONFIG.copy()` then `.update(saved_config)` — top-level keys only, nested dicts like `urls` are fully replaced
- **Browser lifecycle**: `BrowserManager` is shared across source downloads; each source gets a fresh `BrowserManager` in CLI mode
- **Constants use UPPERCASE**: `ALLOWED_EXTENSIONS`, `EXCLUDED_EXTENSIONS`, `EXCLUDED_PREFIXES` in `audio_downloader/constants.py` — always reference them with exact uppercase names

## Dependencies

`selenium`, `webdriver-manager`, `psutil`, `watchdog`, `pyinstaller` (+ `ffmpeg` system package)

## CI

GitHub Actions (`.github/workflows/windows_build.yml`): builds Windows exe on push to `main`/`master` and on semver tags. Releases created for tags.

## Config Management

`download_config.json` is gitignored and auto-created from `DEFAULT_CONFIG` on first run. Key fields that users must set:

- **`cow_password`**: Clear Out West password
- **`urls`**: Real Dropbox shared links per source (defaults are `YOUR_LINK_HERE` placeholders)
- **`output_dir`**: Base output directory (defaults to `downloads/`). All source folders are created under this.

To update config programmatically, use `ConfigManager`:
```python
from audio_downloader.config import ConfigManager
cm = ConfigManager()
cm.set("output_dir", "/path/to/output")
cm.save()
```

## Adding New Download Sources

New sources require registration in **4 places**:

1. **Create source module**: `audio_downloader/sources/<snake_case_name>.py` with a class inheriting from `BaseDownloader`, implementing `download(update_callback=None) -> bool`

2. **Register in factory** (`audio_downloader/sources/__init__.py`):
   - Add import: `from .<snake_case_name> import <CamelCaseName>Downloader`
   - Add to `downloaders` dict in `create_downloader()`: `"Display Name": <CamelCaseName>Downloader`

3. **Register in config** (`audio_downloader/config.py`):
   - Add to `DOWNLOAD_SOURCES` dict: `"Display Name": "snake_case_name"`

4. **Register in PyInstaller spec** (`AudioDownloader.spec`):
   - Add to `hiddenimports` list: `'audio_downloader.sources.<snake_case_name>'`
   - This is critical — PyInstaller won't auto-discover dynamically imported source modules, and the exe will crash on that source.

After adding a source, verify:
```bash
python -c "from audio_downloader.sources import create_downloader; from audio_downloader.browser_manager import BrowserManager; from audio_downloader.config import ConfigManager; bm = BrowserManager(ConfigManager()); d = create_downloader('Display Name', bm, ConfigManager()); print('OK')"
```

## Release Workflow

To publish a new version:

1. **Bump version** in `audio_downloader/__init__.py`:
   ```python
   __version__ = "1.1.9"  # Use semver (major.minor.patch)
   ```

2. **Commit** the change:
   ```bash
   git add audio_downloader/__init__.py
   git commit -m "chore: bump version to 1.1.9"
   ```

3. **Create and push a semver tag**:
   ```bash
   git tag 1.1.9
   git push origin main --tags
   ```

4. **CI does the rest**: The tag triggers `.github/workflows/windows_build.yml` which:
   - Builds `dist/AudioDownloader.exe` via PyInstaller
   - Creates a GitHub Release at `wardbryan3/SeleniumDownloader/releases` with the exe attached

## Updating the Executable Locally

For local builds (before pushing):

```bash
pyinstaller --clean AudioDownloader.spec
```

Output: `dist/AudioDownloader.exe`

The `.spec` file's `hiddenimports` list must be kept in sync whenever modules are added or removed. If a new module is added (not in `audio_downloader/sources/`), add it to `hiddenimports` — PyInstaller cannot detect runtime-imported modules like those in the factory pattern.

The `AudioDownloader.exe` reads config from the same directory it's placed in (`download_config.json` auto-created on first run). It does not bundle FFmpeg — FFmpeg must be separately available on the user's system PATH for tag overlay to work.
