# Linux Audio Download Automation — Summary and Plan

## Goal

Move every audio download to one always-on Ubuntu Server host on the station network. The host reaches administration only through Tailscale SSH, downloads and validates content automatically, then publishes finished files to Dropbox through the official Linux Dropbox daemon.

Linux becomes production download host. Existing Windows jobs may overlap during early production; same filenames make duplicate downloads acceptable. Disable Windows tasks after one clean Linux week.

## Production Platform

- **Host:** always-on x86_64 Ubuntu Server 24.04 LTS; Pacific timezone configured as `America/Los_Angeles` (handles PST/PDT).
- **Access:** Tailscale-only SSH. No public inbound ports.
- **Runtime:** dedicated unprivileged service account, Python virtual environment, `systemd` services and timers.
- **Dropbox:** official headless Dropbox daemon under service account. It syncs station-visible folders only.
- **Secrets:** root/service-user-owned `.env`, permissions `0600`, outside Git and Dropbox. Holds provider credentials, shared URLs, Gmail app password, and API keys. Never put secrets in Markdown, source code, logs, fixtures, or committed config.
- **State:** SQLite database outside Dropbox records source IDs/dates, content hashes, duration/size checks, first-seen times, attempts, outcomes, and Dropbox-daemon health.
- **Staging:** download into local non-Dropbox staging directory. Validate fully, then atomically rename into Dropbox folder. Dropbox never sees partial files.

## File Contract

Preserve current station-visible Dropbox layout and existing cart filenames:

- `GLOBAL FEATURES/`
- `Promos/`
- `NBC/`

Stable carts overwrite only after validated replacement. If new weekly content is absent, retain old cart, mark it stale in state/reporting, and email an alert. Do not silently report success.

No dated archive is required. SQLite and run reports provide operational history.

## Sources and Delivery Rules

| Source                   | Transport target                              | Required output / behavior                                                                                                                                                                                                      |
| ------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Melinda Myers            | Direct FTP preferred; replace Selenium        | Validate date/episode identity; publish five stable weekday carts: `MMMON.mp3`, `MMTUE.mp3`, `MMWED.mp3`, `MMTHU.mp3`, `MMFRI.mp3`.                                                                                             |
| Northwest Outdoors       | Direct HTTP download from Dropbox shared link | Download ZIP once; publish show files to `GLOBAL FEATURES/`; process promo as current application does.                                                                                                                         |
| Northwest Outdoors promo | Extract from same NWO ZIP                     | Preserve existing FFmpeg station-tag overlay behavior and current promo destination/name. Validate FFmpeg and tag asset before publish.                                                                                         |
| Whittler                 | Direct HTTP download from Dropbox shared link | Extract and map Parts A–D to `Whittler1.mp3`–`Whittler4.mp3`.                                                                                                                                                                   |
| Clear Out West           | Direct HTTP session preferred                 | Implement authenticated form/session request flow. Temporary isolated headless Firefox fallback is allowed only while direct flow is unverified; alert when fallback is used. Publish COW tracks and promo under current names. |
| Weekend In The Country   | FTP                                           | Download show segments and promos; retain current segment/promo naming and selection logic, including upcoming Saturday promo selection.                                                                                        |
| AgInfo                   | Direct HTTP                                   | Publish `AGRIBIZ.mp3`, `MARKETAG.mp3`, and `LOA.mp3`. Replace PowerShell BITS, which fails when provider omits `Content-Length`, with streaming HTTP client logic.                                                              |
| RODEOSHOW                | Direct HTTP                                   | Existing PowerShell URL has no successful-download evidence. Treat as required but unverified until first live probe proves endpoint, naming, and validation rules.                                                             |
| NBC / TTWN News-247      | TTWN API                                      | Poll `newFiles`; download each returned provider URL. Preserve current provider filenames in `NBC/`; overwrite only same filename. No-new-files response is normal.                                                             |

## Scheduling

### Weekly feeds

1. Start Sunday at 11:00 PM Pacific.
2. For each failed or incomplete source, retry three times after **5, 15, and 60 minutes**.
3. Retry only missing/failed sources nightly through Friday at 11:00 PM Pacific.
4. Successful sources do not re-download merely because another source failed.
5. Require every source's expected outputs before reporting weekly success.

Sunday-first polling is source-of-truth. Current inferred availability is not a contract:

- Melinda Myers is uploaded ahead of air date.
- Weekend In The Country is typically available Tuesday.
- Prior design estimated Northwest Outdoors, Whittler, and Clear Out West by Monday, and Northwest promo by Tuesday.

System must record first-seen availability, IDs/dates, and validation results for every poll. After 4–8 weeks, use this evidence to document actual posting patterns; confirm provider schedules where practical.

### NBC

- Run at `:15` and `:45` Pacific, 24/7.
- Use lock to skip overlapping runs.
- `newFiles` empty response is successful idle state.
- After two consecutive failed polls, send failure email; send recovery email on next successful poll.

## Validation and Publishing

A successful network response is insufficient. Before publish, validate each expected file using:

1. Source ID/date/episode metadata when available.
2. Expected filename/cart mapping.
3. Non-zero size and source-specific minimum size/duration.
4. Audio readability and duration via `ffprobe`.
5. SHA-256 checksum against SQLite state to identify change/repeat behavior.
6. ZIP/FTP extraction completeness where applicable.
7. Dropbox daemon running and healthy before publish.

Do not use acoustic fingerprinting initially. It adds complexity and false-match risk. Add only if a source lacks reliable IDs/dates and duration/hash checks cannot distinguish content.

## Alerts and Reporting

Use dedicated Gmail automation account with Gmail SMTP app password stored in `.env`.

- Email immediate weekly-source failure after immediate retries exhaust.
- Email nightly retry failures until recovery or Friday cutoff.
- Email NBC after two consecutive failed polls and on recovery.
- Send weekly completion summary: per-source status, stale carts, attempt counts, source metadata, validation results, Dropbox-daemon state, and unresolved blockers.
- Persist detailed logs outside Dropbox with rotation.

## Existing-State Findings

- Current application on `main` is Windows/Firefox-oriented and runs five primary sources sequentially. `--download-all` does **not** include Northwest promo.
- Existing Windows batch files split global-feature run (Thursday 11 PM) and promo run (Tuesday 11 PM).
- Existing PowerShell AgInfo job runs nightly; repeated BITS failures occur when response lacks `Content-Length`.
- Existing NBC Windows batch uses TTWN `newFiles`, `curl`, temp staging, same-name Dropbox overwrite, and 90-day daily logs. It has no persistent state, validation, retry policy, health check, or email alerts.
- A previous unmerged branch, `origin/fix/promo-fixes`, contains `docs/superpowers/specs/2026-06-26-weekly-automation-design.md`. It proposes direct FTP/HTTP downloads, single weekly schedule, source parallelism, and WITC promo integration. Port useful behavior and tests onto current `main`; do not merge stale Windows assumptions wholesale.
- Existing copied NBC batch contains plaintext provider API credential. Do not rotate it per operator decision. Remove it from shared archives/scripts before deployment; store it only in deployment `.env` with `0600` permissions.

## Implementation Sequence

1. **Recover baseline:** Compare `main` with `origin/fix/promo-fixes`; port useful package layout, tests, WITC promo behavior, and direct-download ideas onto new Linux-focused design.
2. **Build core runtime:** Add `.env` loader, validated typed source configuration, SQLite state/migrations, structured logging, staging/publish module, Dropbox health probe, Gmail notifier, lock handling, and CLI result/report model.
3. **Replace transports:** Implement direct FTP/HTTP/API downloaders for Melinda, NWO, Whittler, WITC, AgInfo, NBC, and RODEOSHOW. Implement COW direct session flow; add headless fallback only if needed.
4. **Encode output contracts:** Define required-file sets, source date/ID extraction, minimum duration/size rules, FFmpeg tag validation, stale-cart behavior, and atomic publishing for every source.
5. **Schedule services:** Create separate systemd services/timers for weekly orchestrator, nightly retry, and NBC half-hour poll. Apply lock and recovery semantics.
6. **Test:** Unit-test parsing, source validation, state transitions, retries, stale behavior, publishing, and notifier policy. Use saved sanitized fixtures for ZIP/FTP/API responses. Run provider probes with live credentials only from deployed host.
7. **Deploy:** Install Dropbox daemon, Python/FFmpeg/ffprobe dependencies, service account, `.env`, systemd units, and Tailscale SSH. Confirm Dropbox health and Gmail delivery.
8. **Cut over:** Run Linux publishing alongside Windows if needed; duplicates are acceptable. Review one clean Linux week, then disable Windows tasks.

## Acceptance Criteria

- Linux host survives reboot and resumes all timers/services automatically.
- All weekly sources produce expected validated carts without GUI interaction.
- NBC polls at `:15`/`:45`, handles empty results as normal, and publishes new provider files.
- No partial, empty, stale-unmarked, or mismatched audio overwrites a stable cart.
- Dropbox daemon is healthy before every publish; final files reach expected Dropbox folders.
- Immediate retry and nightly retry rules occur exactly as defined.
- Failure/recovery/weekly-summary emails deliver through dedicated Gmail account.
- SQLite proves content identity, availability timing, validation, retries, and publication decisions.
- RODEOSHOW is included only after successful live verification; until then it appears as explicit unresolved source failure, never silent success.
