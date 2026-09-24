# Provider probe notes

**Probe host:** `lessons-vm`
**Probe date:** 2026-09-22 Pacific
**Safety:** Downloads stayed in `/tmp`; no Dropbox publishing occurred. Credentials, private URLs, and API keys are intentionally absent.

## Results

| Source | Result | Observed contract / blocker |
|---|---|---|
| Melinda Myers | Verified | Explicit FTPS works with certificate-valid host `myers002.trivera.com`. Provider splits coming-week carts across `3x` (Mon/Wed/Fri) and `5x` (Tue/Thu) directories. Audio names begin `MMDDYY_`; five staged carts downloaded successfully. FTP listing/download timeouts allow five minutes for provider slowness. |
| Northwest Outdoors | Verified | Shared Dropbox archive (86 MB) contains stable `NWoutdoors1`–`5` segment members, `NWoutdoors_promo`, and a dated full-program member. Adapter selects only six stable members, tags promo in staging, and passes ffprobe validation. |
| Whittler | Verified archive | Shared download returned a 118 MB ZIP. Current show has Parts A-D; archive also contains unrelated historical audio, so parser must select only current Parts A-D. |
| Weekend In The Country | Verified, insecure transport | Explicit FTPS is unavailable. With operator authorization, plain-FTP adapter fetched eight current segments and nearest upcoming-Saturday promo (nine files total); ffprobe validation passed. Do not poll excessively; provider warns that frequent logins may block station access. |
| Clear Out West | Verified session flow | HTTPS form login succeeds when `requests.Session` sends browser-like User-Agent, preserves `redirect` and `u` hidden fields, and posts password as `p`. Authenticated page exposes five MP3 links. |
| AgInfo / RODEOSHOW | Verified | Working Windows `Download-Audio.ps1` groups three AgInfo feeds and RODEOSHOW in one nightly run. AgInfo streams returned `200 audio/mpeg` without `Content-Length` (3.5–3.7 MB); RODEOSHOW passed direct HTTP and ffprobe validation. Log shows daily execution at approximately 22:11 Pacific, including weekends. |
| RODEOSHOW | Verified | Direct HTTP adapter staged 4.3 MB (`4,331,520` bytes) and passed ffprobe validation. |
| NBC / TTWN | Verified | Authenticated `newFiles` call returned `200 text/plain` with an empty line manifest (`idle`). API uses `X-API-Key`, affiliate path, and provider URLs listed one per line; not JSON. |

## Implementation consequences

1. Keep Melinda parser limited to verified `MMDDYY_` names; do not add speculative date formats.
2. Northwest selects five stable `NWoutdoors1`–`5` carts plus `NWoutdoors_promo` and ignores dated full-program member. Dropbox shared-folder URLs use `dl=1`; host must provide tag WAV at configured protected path.
3. Keep Whittler Part A-D parser and explicitly reject archive noise.
4. WITC uses explicit authorized plain-FTP only, records `insecure_transport`, and persists an insecure-transport message with successful run state. Limit attempts to scheduled runs and immediate retry policy only.
5. COW uses HTTPS form sessions: preserve cookies and hidden fields, post `p`, and require exactly five contracted MP3 links. Browser fallback remains deliberately absent.
6. NBC adapter must use `X-API-Key`, `<api-url>/<affiliate>/newFiles`, line-manifest parsing, same-name overwrites, and `idle` on empty manifest. Keep two-failure/recovery notification policy.
7. Run AgInfo and RODEOSHOW together every day at 22:11 Pacific. Keep both out of weekly retry semantics.
8. RODEOSHOW uses direct HTTP with a `RODEOSHOW.mp3` contract and a 1 MB minimum-size guard before common ffprobe, hash, Dropbox-health, and atomic-publish processing.
