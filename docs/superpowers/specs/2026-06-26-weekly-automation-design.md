# Weekly Download Automation Design

## Overview

Consolidate the radio show download pipeline into a single automated weekly run. Replace browser-based scraping with direct HTTP/FTP downloads where possible, parallelize independent sources, and integrate the WITC promo rename logic into the downloader itself.

## Goals

- One scheduled task downloads everything for the coming week
- Eliminate browser dependency for all sources except Clear Out West (phase 2: eliminate entirely if feasible)
- Parallelize downloads for speed
- All cart filenames remain stable (automation system reads folders directly)
- No stale content — everything fresh before it airs

## Schedule

### Single run: Tuesday 11:00 PM via Windows Task Scheduler

One bat script: `scripts/download_weekly.bat`

```bat
@echo off
cd /d "%~dp0.."
AudioDownloader.exe --download-all
```

### Why Tuesday

All content is available by Monday except the Northwest Outdoors promo, which updates Tuesday. Tuesday night is the earliest point where everything can be fetched in one pass. With a month of Melinda Myers content on FTP, the coming week's tips are always available.

### Air schedule vs. download timing

| Source | Airs | Content available | Downloaded |
|---|---|---|---|
| Melinda Myers | Mon-Fri | ~1 month ahead (FTP) | Previous Tuesday |
| WITC promo | Throughout week | By Monday (FTP) | Tuesday 11PM |
| WITC show | Saturday morning | By Monday (FTP) | Tuesday 11PM |
| NW Outdoors show | Saturday | By Monday | Tuesday 11PM |
| NW Outdoors promo | Saturday | By Tuesday | Tuesday 11PM |
| Whittler | Sunday | By Monday | Tuesday 11PM |
| Clear Out West | Sunday | By Monday | Tuesday 11PM |

Everything airs fresh. Melinda Myers for the coming Mon-Fri is downloaded the prior Tuesday — no stale gap.

## Source Changes

### 1. Melinda Myers — Rewrite to FTP

**Current:** Selenium web scraping of melindamyers.com, downloading day-by-day
**New:** FTP download, like WITC

Flow:
1. Connect to MM FTP server using configured credentials
2. List all MP3 files recursively
3. Extract dates from filenames (regex, flexible format — try MM-DD-YY, MMDDYY, YYYY-MM-DD)
4. Find files matching the coming week's Mon, Tue, Wed, Thu, Fri dates
5. Download those 5 files
6. Rename to stable cart filenames:
   - `MMMON.mp3` (Monday)
   - `MMTUE.mp3` (Tuesday)
   - `MMWED.mp3` (Wednesday)
   - `MMTHU.mp3` (Thursday)
   - `MMFRI.mp3` (Friday)
7. Place in `GLOBAL FEATURES/`

Config additions:
```json
{
    "mm_ftp_server": "",
    "mm_ftp_username": "",
    "mm_ftp_password": ""
}
```

### 2. Northwest Outdoors — Direct HTTP download, merge show + promo

**Current:** Two separate Selenium runs, each downloads the same Dropbox ZIP
**New:** Single `requests.get(url + "?dl=1")` download, extract once, split show vs. promo

Flow:
1. Download ZIP via direct HTTP (`requests` library, `?dl=1` parameter)
2. Extract to temp directory
3. Non-promo, non-date-stamped files → `GLOBAL FEATURES/` (show content)
4. Promo files → `Promos/` with tag overlay (existing `DownloadUtilities.overlay_promo_with_tag` logic)
5. Clean up temp directory

Eliminates: redundant ZIP download, browser startup, XPath waiting, popup handling.

### 3. Whittler — Direct HTTP download

**Current:** Selenium + Dropbox ZIP download
**New:** `requests.get(url + "?dl=1")` direct download

Flow:
1. Download ZIP via direct HTTP
2. Extract to temp directory
3. Map "Part A/B/C/D" to `Whittler1.mp3`–`Whittler4.mp3` (existing logic)
4. Place in `GLOBAL FEATURES/`
5. Clean up temp directory

### 4. Clear Out West — Phase 1: Keep Selenium, Phase 2: Investigate requests

**Phase 1 (this design):** Keep Selenium-based download as-is. It requires password login on clearoutwest.com, which is a simple HTML form POST that could be done with `requests` but needs investigation first.

**Phase 2 (future):** Replace with `requests.Session()` — POST password to login form, follow redirect, download MP3/ZIP links directly. If feasible, eliminates the last browser dependency.

### 5. Weekend In The Country — Integrate promo rename

**Current:** FTP download + separate `witc_promo_rename.bat` for promo rename
**New:** FTP download + integrated promo rename in `_process_files()`

The FTP server provides two promos: this week's and next week's.

Flow:
1. Connect to WITC FTP (existing logic)
2. Download all MP3 files (existing logic)
3. Rename segments to `WITC_HR{hr}_PT{pt}.mp3` in `GLOBAL FEATURES/` (existing logic)
4. Rename promos to `WITC_PROMO_MM-DD-YY.mp3` in `Spots/` (existing logic)
5. **NEW:** Find the upcoming Saturday's date
6. **NEW:** Copy `WITC_PROMO_{upcoming-saturday}.mp3` to `WITC_PROMO.mp3` (stable cart)
7. **NEW:** Delete any `WITC_PROMO_*.mp3` files dated before the upcoming Saturday
8. **NEW:** Preserve `WITC_PROMO_*.mp3` files dated after the upcoming Saturday (next week's promo)

This replaces the fragile `witc_promo_rename.bat` PowerShell script and fixes the bug where next week's promo was being deleted.

## Parallelization

### Architecture: ThreadPoolExecutor with source groups

```
ThreadPoolExecutor(max_workers=5):
  Thread 1: Melinda Myers (FTP)
  Thread 2: WITC (FTP)
  Thread 3: NW Outdoors show + promo (HTTP)
  Thread 4: Whittler (HTTP)
  Thread 5: Clear Out West (Selenium — only browser source)
```

All sources run concurrently. FTP and HTTP sources are pure I/O — no browser, no shared download directory, no conflicts. Clear Out West gets its own `BrowserManager` instance.

**Key changes to enable parallelization:**
- Each source gets its own temp directory (not shared `browser_downloads/`)
- Each browser source gets its own `BrowserManager` (already supported — CLI mode creates fresh managers)
- `run_cli_downloads()` uses `ThreadPoolExecutor` instead of sequential loop
- Thread-safe result collection and logging
- NW Outdoors promo download merged into NW Outdoors show download (single ZIP, split locally)

**GIL consideration:** Not a problem. All sources are I/O-bound (network waits, file writes, `time.sleep`). The GIL releases during I/O operations.

### Error handling

- Each source runs in its own thread with try/except
- Failures are collected, not fatal — one source failing doesn't stop others
- Final summary reports per-source success/failure
- Exit code: 0 if all succeeded, 1 if any failed (same as current behavior)

## CLI Changes

### `--download-all` (modified)

Currently downloads 5 sources sequentially in one browser. New behavior:
- Downloads all sources in parallel via ThreadPoolExecutor
- Includes NW Outdoors promo (currently excluded — was a separate `--download-promo` run)
- No shared browser — each source manages its own transport

### `--download-promo` (deprecated)

Merged into `--download-all`. Kept for backward compatibility but calls the merged NW Outdoors download.

### `--source` (unchanged)

Single-source download still works for manual re-downloads.

## File Changes Summary

### New files
- `scripts/download_weekly.bat` — single weekly bat script

### Modified files
- `audio_downloader/sources/melinda_myers.py` — full rewrite to FTP
- `audio_downloader/sources/northwest_outdoors.py` — rewrite to HTTP, merge show + promo
- `audio_downloader/sources/whittler.py` — rewrite to HTTP
- `audio_downloader/sources/weekend_in_the_country.py` — add promo rename to `_process_files()`
- `audio_downloader/main.py` — parallelize `run_cli_downloads()`, include promo in `--download-all`
- `audio_downloader/config.py` — add MM FTP credentials to `DEFAULT_CONFIG`
- `AudioDownloader.spec` — add `requests` to hiddenimports if needed

### Deleted files
- `scripts/witc_promo_rename.bat` — logic moved into WITC downloader
- `scripts/download_promos.bat` — merged into `--download-all`
- `scripts/download_global_features.bat` — replaced by `download_weekly.bat`

## Dependencies

### New
- `requests` — HTTP downloads for Dropbox sources (NW Outdoors, Whittler)

### Potentially removable (future)
- `selenium` — only needed for Clear Out West after this redesign
- `webdriver-manager` — same

### Unchanged
- `psutil`, `watchdog`, `pyinstaller`
- `ffmpeg` — system package, still needed for tag overlay

## Cart Filename Reference

| Source | Folder | Cart filenames |
|---|---|---|
| Melinda Myers | GLOBAL FEATURES/ | MMMON.mp3, MMTUE.mp3, MMWED.mp3, MMTHU.mp3, MMFRI.mp3 |
| NW Outdoors (show) | GLOBAL FEATURES/ | Original ZIP filenames (non-promo, non-date-stamped) |
| NW Outdoors (promo) | Promos/ | Original promo filename from ZIP (with tag overlay) |
| Whittler | GLOBAL FEATURES/ | Whittler1.mp3, Whittler2.mp3, Whittler3.mp3, Whittler4.mp3 |
| Clear Out West | GLOBAL FEATURES/ | COW1.mp3, COW2.mp3, ..., COWPROMO.mp3 |
| WITC (show) | GLOBAL FEATURES/ | WITC_HR{hr}_PT{pt}.mp3 |
| WITC (promo) | Spots/ | WITC_PROMO.mp3 (stable), WITC_PROMO_MM-DD-YY.mp3 (dated) |

## Open Questions

1. **Melinda Myers FTP date format** — Need to confirm the exact date format in filenames. Design uses flexible regex to try multiple formats. Verify against actual FTP listing before implementation.

2. **Clear Out West via requests** — Phase 2 investigation. The login is a simple HTML form POST that may work with `requests.Session()`. If feasible, eliminate the last browser dependency entirely.

3. **Dropbox `?dl=1` reliability** — The `?dl=1` parameter has been stable for years but is not officially documented for shared folder links. If it breaks, fall back to the Dropbox API SDK (`dropbox` package) which supports shared link downloads without authentication.