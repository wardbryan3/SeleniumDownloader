"""
Weekend In The Country download source (FTP)
"""

import re
import logging
from pathlib import Path

from .base import BaseDownloader

logger = logging.getLogger(__name__)


class WeekendInTheCountryDownloader(BaseDownloader):
    """Download Weekend In The Country files via FTP"""
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING WEEKEND IN THE COUNTRY DOWNLOAD ===")

        server = self.config_manager.get("witc_ftp_server", "")
        username = self.config_manager.get("witc_ftp_username", "")
        password = self.config_manager.get("witc_ftp_password", "")

        if not server or not username or not password:
            logger.error("FTP credentials not configured for Weekend In The Country")
            if update_callback:
                update_callback(100, "Error: FTP credentials not configured")
            return False

        if update_callback:
            update_callback(10, "Connecting to FTP server...")

        from ftplib import FTP

        ftp = FTP()
        try:
            ftp.connect(server, timeout=30)
            ftp.login(username, password)
            ftp.encoding = 'utf-8'
        except Exception as e:
            logger.error(f"FTP connection/login failed for {server}: {e}")
            if update_callback:
                update_callback(100, f"Error: FTP connection/login failed: {e}")
            try:
                ftp.close()
            except Exception:
                pass
            return False

        logger.info(f"Connected to {server}")

        output_dir = Path(self.config_manager.get_global_features_dir())
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if update_callback:
                update_callback(20, "Finding MP3 files...")

            mp3_files = self._find_mp3_files(ftp)

            if not mp3_files:
                logger.warning("No MP3 files found on FTP server")
                if update_callback:
                    update_callback(100, "No MP3 files found")
                return False

            logger.info(f"Found {len(mp3_files)} MP3 file(s)")
            if update_callback:
                update_callback(30, f"Found {len(mp3_files)} MP3 file(s)")

            downloaded = 0
            for i, remote_path in enumerate(mp3_files):
                filename = Path(remote_path).name
                local_path = output_dir / filename

                if local_path.exists():
                    logger.info(f"Skipping (already exists): {filename}")
                    continue

                if update_callback:
                    progress = 30 + int((i / len(mp3_files)) * 60)
                    update_callback(progress, f"Downloading {filename}...")

                logger.info(f"Downloading: {remote_path}")

                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {remote_path}', f.write)

                logger.info(f"Downloaded: {filename}")
                downloaded += 1

            if update_callback:
                update_callback(100, f"Downloaded {downloaded} file(s)")

            self._process_files(output_dir)

            logger.info(f"=== WEEKEND IN THE COUNTRY DOWNLOAD COMPLETE ({downloaded} files) ===")
            return True

        except Exception as e:
            logger.error(f"Error in Weekend In The Country download: {e}")
            import traceback
            traceback.print_exc()
            if update_callback:
                update_callback(100, f"Error: {e}")
            return False
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    def _process_files(self, output_dir):
        """Rename downloaded files to WITC naming convention"""
        seg_re = re.compile(r'hr(\d+)_seg(\d+)', re.IGNORECASE)
        date_re = re.compile(r'(\d{2}-\d{2}-\d{2})')
        promos = []
        segments = []

        for f in output_dir.iterdir():
            if not f.is_file() or not f.name.lower().endswith('.mp3'):
                continue
            if not f.name.startswith('Weekend in the Country'):
                continue

            name = f.name
            seg_match = seg_re.search(name)
            if seg_match:
                segments.append((f, seg_match.group(1), seg_match.group(2)))
                continue

            if 'promo' in name.lower():
                date_match = date_re.search(name)
                promos.append((f, date_match.group(1) if date_match else ''))

        for f, hr, pt in segments:
            new_name = f.parent / f"WITC_HR{hr}_PT{pt}.mp3"
            try:
                f.rename(new_name)
                logger.info(f"Renamed: {f.name} -> {new_name.name}")
            except OSError as e:
                logger.warning(f"Failed to rename {f.name}: {e}")

        spots_dir = Path(self.config_manager.get_spots_dir())
        spots_dir.mkdir(parents=True, exist_ok=True)

        for f, date_str in promos:
            date_tag = f"_{date_str}" if date_str else ""
            new_name = spots_dir / f"WITC_PROMO{date_tag}.mp3"
            try:
                f.rename(new_name)
                logger.info(f"Moved promo: {f.name} -> {new_name}")
            except OSError as e:
                logger.warning(f"Failed to move promo {f.name}: {e}")

    def _find_mp3_files(self, ftp, path=""):
        """Recursively find all MP3 files on the FTP server"""
        mp3_files = []

        try:
            items = []
            ftp.retrlines(f'LIST {path}', items.append)
        except Exception as e:
            logger.warning(f"Cannot list path '{path}': {e}")
            return mp3_files

        for line in items:
            try:
                parts = line.split()
                if len(parts) < 9:
                    continue

                name = ' '.join(parts[8:]).strip()
                if not name or name in ('.', '..'):
                    continue

                full_path = f"{path}/{name}" if path else name
                is_dir = parts[0].startswith('d')

                if is_dir:
                    mp3_files.extend(self._find_mp3_files(ftp, full_path))
                elif name.lower().endswith('.mp3'):
                    mp3_files.append(full_path)
            except Exception as e:
                logger.warning(f"Error parsing listing line '{line}': {e}")
                continue

        return mp3_files
