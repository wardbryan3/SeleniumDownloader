# [file name]: download_utils.py
"""
Download utilities for monitoring and file handling
"""

import os
import sys
import time
import subprocess
import logging
import psutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DownloadUtilities:
    """Utility functions for download monitoring"""
    
    @staticmethod
    def get_file_hash(file_path: str, block_size: int = 65536) -> str:
        """Generate MD5 hash of a file"""
        import hashlib
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hasher.update(block)
            return hasher.hexdigest()
        except Exception as e:
            logger.debug(f"Error hashing file {file_path}: {e}")
            return ""
    
    @staticmethod
    def is_file_locked(filepath: str) -> bool:
        """Check if a file is locked/opened by another process"""
        try:
            # Try to open the file in exclusive mode
            with open(filepath, 'rb'):
                return False
        except IOError:
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_handle_count(filepath: str) -> int:
        """Get the number of open handles to a file"""
        try:
            filepath = os.path.abspath(filepath)
            count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for item in proc.open_files():
                        if item.path == filepath:
                            count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except Exception as e:
            logger.debug(f"Error checking file handles for {filepath}: {e}")
            return 0
    
    @staticmethod
    def find_latest_file(download_dir: str, extension: str = None, wait_time: int = 2):
        """Find the most recently downloaded file after waiting"""
        time.sleep(wait_time)
        download_path = Path(download_dir).resolve()
        
        if not download_path.exists():
            return None
        
        all_files = []
        for file_path in download_path.iterdir():
            if file_path.is_file():
                if extension is None or str(file_path).endswith(extension):
                    if any(str(file_path).endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download']):
                        continue
                    try:
                        if file_path.stat().st_size > 0:
                            all_files.append(str(file_path))
                    except OSError:
                        continue
        
        if not all_files:
            return None
        
        try:
            newest_file = max(all_files, key=lambda f: Path(f).stat().st_mtime)
            
            size1 = Path(newest_file).stat().st_size
            time.sleep(0.5)
            size2 = Path(newest_file).stat().st_size
            
            if size1 == size2 and size1 > 0:
                return newest_file
            else:
                time.sleep(1)
                return newest_file
                
        except Exception as e:
            logger.error(f"Error finding latest file: {e}")
            return None

    @staticmethod
    def _get_audio_duration(file_path: str) -> Optional[float]:
        """Get audio duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        return None

    @staticmethod
    def overlay_promo_with_tag(promo_file: str, tag_file: str, output_file: str,
                                overlap_seconds: int = 10) -> bool:
        """
        Keep the full promo except the last N seconds, then append the last
        N seconds mixed with the tag file so both play simultaneously.

        Args:
            promo_file: Path to the promo MP3 file
            tag_file: Path to the WAV tag file
            output_file: Path for the output MP3 file
            overlap_seconds: How many seconds to overlap (default: 10)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing promo: {promo_file} with tag overlay")

        if not Path(promo_file).exists():
            logger.error(f"Promo file not found: {promo_file}")
            return False

        if not Path(tag_file).exists():
            logger.error(f"Tag file not found: {tag_file}")
            return False

        promo_duration = DownloadUtilities._get_audio_duration(promo_file)
        if promo_duration is None or promo_duration <= overlap_seconds:
            logger.warning(
                f"Could not determine promo duration ({promo_duration}s), "
                f"skipping tag overlay"
            )
            return False

        pre_duration = promo_duration - overlap_seconds
        filter_complex = (
            f'[0:a]atrim=0:{pre_duration},asetpts=PTS-STARTPTS[pre];'
            f'[0:a]atrim=start={pre_duration},asetpts=PTS-STARTPTS[ending];'
            f'[ending][1:a]amix=inputs=2:duration=first:normalize=0[mixed];'
            f'[pre][mixed]concat=n=2:v=0:a=1[out]'
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', promo_file,
            '-i', tag_file,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-codec:a', 'libmp3lame',
            '-q:a', '2',
            output_file,
        ]

        create_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        try:
            logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=create_flags,
            )

            if result.returncode == 0 and Path(output_file).exists():
                logger.info(f"Promo with tag saved to {output_file}")
                return True
            else:
                logger.error(f"FFmpeg returncode: {result.returncode}")
                if result.stderr:
                    logger.error(f"FFmpeg stderr: {result.stderr[:1000]}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out")
            return False
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            logger.error(f"Error creating promo with tag: {e}")
            return False
