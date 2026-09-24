# Linux deployment and host transfer

All deployable files live in this repository. A host needs only a checked-out release, a separately managed protected environment file, Dropbox setup, and `deploy/install-ubuntu.sh`.

## VM validation: `lessons-vm`

`lessons-vm` is Ubuntu 24.04-compatible (`systemd 255`, Python 3.12). Use it for install and timer validation only. Do not add production credentials, connect production Dropbox, or enable real source timers there.

```sh
ssh lessons-vm
cd /path/to/SeleniumDownloader
cp deploy/audio-downloader.env.example /tmp/audio-downloader.env
# Fill no credentials for dry run.
sudo deploy/install-ubuntu.sh --repo-dir "$PWD" --env-file /tmp/audio-downloader.env --dry-run
```

## New physical host

1. Install Ubuntu 24.04, set timezone, and clone a tagged release. Installer adds Python venv support and FFmpeg.

   ```sh
   sudo timedatectl set-timezone America/Los_Angeles
   git clone <repository-url> /srv/audio-downloader-release
   cd /srv/audio-downloader-release
   ```

2. Create host-only configuration from tracked template. This is intentional: template is tracked; filled file is not.

   ```sh
   sudo install -d -m 750 -o root -g root /root/audio-downloader-secrets
   sudo cp deploy/audio-downloader.env.example /root/audio-downloader-secrets/audio-downloader.env
   sudo chmod 600 /root/audio-downloader-secrets/audio-downloader.env
   sudoedit /root/audio-downloader-secrets/audio-downloader.env
   ```

   Put provider, Gmail, and TTWN credentials only in this host file. Never copy it into repo, Dropbox, archive, fixture, or support ticket.

3. Configure official Dropbox daemon under `audio-downloader` account. Point `AUDIO_OUTPUT_ROOT` at its synced folder. Confirm `pgrep -u audio-downloader dropbox` succeeds before enabling timers.

4. Install tracked release and systemd units.

   ```sh
   sudo deploy/install-ubuntu.sh \
     --repo-dir "$PWD" \
     --env-file /root/audio-downloader-secrets/audio-downloader.env
   sudo systemctl start audio-downloader-weekly.timer \
     audio-downloader-nightly.timer audio-downloader-aginfo.timer audio-downloader-nbc.timer
   systemctl list-timers 'audio-downloader-*'
   ```

5. Validate before cutover.

   ```sh
   sudo -u audio-downloader /opt/audio-downloader/venv/bin/python -m audio_downloader --json report
   sudo systemctl status audio-downloader-nbc.timer
   journalctl -u audio-downloader-nbc.service -n 100 --no-pager
   ```

Do not disable Windows jobs until a full Linux week reports every verified source successful. AgInfo and RODEOSHOW run together daily at 22:11 Pacific.

## Upgrades and transfer

Repeat installation from a new tagged checkout and same protected environment file transfer method. Installer replaces only `/opt/audio-downloader` and tracked unit files; state lives in `/var/lib/audio-downloader`, so back it up before replacement:

```sh
sudo systemctl stop audio-downloader-weekly.timer audio-downloader-nightly.timer audio-downloader-aginfo.timer audio-downloader-nbc.timer
sudo tar -C /var/lib -czf /root/audio-downloader-state-$(date +%F).tgz audio-downloader
```

Transfer state archive through approved encrypted admin channel. Restore ownership to `audio-downloader:audio-downloader`; do not transfer Dropbox data or secret env through Git.
