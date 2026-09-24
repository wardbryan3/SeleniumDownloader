#!/bin/sh
# Install tracked release into a reproducible Linux host layout.
set -eu

REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
INSTALL_ROOT=/opt/audio-downloader
ENV_FILE=
DRY_RUN=false

usage() {
    echo "Usage: $0 --env-file /secure/audio-downloader.env [--repo-dir DIR] [--install-root DIR] [--dry-run]" >&2
    exit 2
}

run() {
    if [ "$DRY_RUN" = true ]; then
        printf '+ %s\n' "$*"
    else
        "$@"
    fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --env-file) ENV_FILE=${2:?}; shift 2 ;;
        --repo-dir) REPO_DIR=${2:?}; shift 2 ;;
        --install-root) INSTALL_ROOT=${2:?}; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) usage ;;
    esac
done

[ "$(id -u)" -eq 0 ] || { echo "Run installer with sudo" >&2; exit 2; }
[ -n "$ENV_FILE" ] || usage
[ -f "$ENV_FILE" ] || { echo "Environment file does not exist" >&2; exit 2; }
[ -f "$REPO_DIR/pyproject.toml" ] || { echo "Repository missing pyproject.toml" >&2; exit 2; }
command -v apt-get >/dev/null || { echo "Ubuntu/Debian apt-get required" >&2; exit 2; }

# Host prerequisites belong here, not in an untracked runbook.
run apt-get update
run env DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv ffmpeg

run groupadd --system audio-downloader 2>/dev/null || true
run id -u audio-downloader >/dev/null 2>&1 || run useradd --system --gid audio-downloader --home /var/lib/audio-downloader --shell /usr/sbin/nologin audio-downloader
run install -d -o audio-downloader -g audio-downloader -m 750 /var/lib/audio-downloader /var/lib/audio-downloader/staging /var/lib/audio-downloader/dropbox
run install -d -o root -g audio-downloader -m 750 /etc/audio-downloader
run install -o root -g audio-downloader -m 640 "$ENV_FILE" /etc/audio-downloader/audio-downloader.env
run install -d -o root -g root -m 755 "$INSTALL_ROOT"
# Install only runtime artifacts. Secrets, Git metadata, tests, and legacy Windows app stay out.
run rm -rf "$INSTALL_ROOT/audio_downloader" "$INSTALL_ROOT/deploy"
run cp -a "$REPO_DIR/audio_downloader" "$REPO_DIR/deploy" "$INSTALL_ROOT/"
run install -o root -g root -m 644 "$REPO_DIR/pyproject.toml" "$INSTALL_ROOT/pyproject.toml"
run chown -R root:root "$INSTALL_ROOT"
run python3 -m venv "$INSTALL_ROOT/venv"
run "$INSTALL_ROOT/venv/bin/pip" install --upgrade pip
run "$INSTALL_ROOT/venv/bin/pip" install "$INSTALL_ROOT"
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-weekly.service" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-weekly.timer" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-nightly.service" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-nightly.timer" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-aginfo.service" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-aginfo.timer" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-nbc.service" /etc/systemd/system/
run install -o root -g root -m 644 "$INSTALL_ROOT/deploy/systemd/audio-downloader-nbc.timer" /etc/systemd/system/
run systemctl daemon-reload
run systemctl enable audio-downloader-weekly.timer audio-downloader-nightly.timer audio-downloader-aginfo.timer audio-downloader-nbc.timer

echo "Installed. Fill protected env, configure Dropbox, then start timers with:"
echo "  sudo systemctl start audio-downloader-weekly.timer audio-downloader-nightly.timer audio-downloader-aginfo.timer audio-downloader-nbc.timer"
