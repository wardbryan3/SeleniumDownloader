# [file name]: download_utils.py
"""
Download utilities for monitoring and file handling
"""

import os
import time
import logging
import glob
import psutil
from pathlib import Path
import threading
import re

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
    def wait_for_download_complete(download_dir: str, expected_extensions=None, 
                                 timeout: int = 30, check_interval: float = 0.5):
        """
        Monitor for new files by checking file handles and locks.
        Uses pathlib for cross-platform path handling.
        """
        if expected_extensions is None:
            expected_extensions = ['.zip', '.mp3']
        
        download_path = Path(download_dir).resolve()
        logger.info(f"Monitoring for downloads in {download_path} (timeout: {timeout}s)")
        
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)
        
        initial_files = set()
        for file_path in download_path.iterdir():
            if file_path.is_file():
                initial_files.add(file_path)
        
        logger.info(f"Initial files in directory: {len(initial_files)}")
        
        start_time = time.time()
        discovered_files = {}
        
        while time.time() - start_time < timeout:
            current_files = set()
            for file_path in download_path.iterdir():
                if file_path.is_file():
                    current_files.add(file_path)
            
            new_files = current_files - initial_files
            
            for file_path in new_files:
                file_str = str(file_path)
                file_name = file_path.name
                
                if file_str in discovered_files and discovered_files[file_str]['completed']:
                    continue
                
                has_valid_extension = any(file_name.endswith(ext) for ext in expected_extensions)
                if not has_valid_extension:
                    is_temp = any(file_name.endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download'])
                    if not is_temp:
                        continue
                
                if file_str not in discovered_files:
                    discovered_files[file_str] = {
                        'first_seen': time.time(),
                        'last_size': 0,
                        'size_changes': 0,
                        'completed': False
                    }
                    logger.debug(f"Discovered new file: {file_name}")
                
                try:
                    current_size = file_path.stat().st_size
                except OSError:
                    continue
                
                record = discovered_files[file_str]
                
                if current_size != record['last_size']:
                    record['last_size'] = current_size
                    record['size_changes'] += 1
                    logger.debug(f"File {file_name} changed size to {current_size}")
                
                is_locked = DownloadUtilities.is_file_locked(file_str)
                handle_count = DownloadUtilities.get_file_handle_count(file_str)
                time_since_discovery = time.time() - record['first_seen']
                
                if (has_valid_extension and
                    time_since_discovery > 2 and
                    current_size > 1024 and
                    not is_locked and
                    handle_count == 0):
                    
                    time.sleep(0.5)
                    try:
                        new_size = file_path.stat().st_size
                        if new_size == current_size:
                            logger.info(f"File complete: {file_name} ({current_size} bytes)")
                            discovered_files[file_str]['completed'] = True
                            return file_str
                    except OSError:
                        continue
                
                is_temp_file = any(file_name.endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download'])
                if is_temp_file and time_since_discovery > 10:
                    base_name = file_path.stem
                    for ext in ['.part', '.crdownload', '.tmp', '.download']:
                        if file_name.endswith(ext):
                            base_name = file_name[:-len(ext)]
                            break
                    
                    for ext in expected_extensions:
                        possible_file = download_path / (base_name + ext)
                        try:
                            if possible_file.exists() and possible_file.stat().st_size > 0:
                                logger.info(f"Found completed file: {possible_file.name}")
                                return str(possible_file)
                        except OSError:
                            continue
            
            time.sleep(check_interval)
        
        logger.warning(f"Download timeout after {timeout} seconds")
        
        for file_str, record in discovered_files.items():
            if record['completed']:
                return file_str
        
        if discovered_files:
            valid_files = []
            for file_str in discovered_files.keys():
                try:
                    if Path(file_str).exists() and Path(file_str).stat().st_size > 0:
                        valid_files.append(file_str)
                except OSError:
                    continue
            
            if valid_files:
                newest_file = max(valid_files, key=os.path.getmtime)
                logger.info(f"Returning newest file: {Path(newest_file).name}")
                return newest_file
        
        return None
    
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

    # Add this method to DownloadUtilities class
    @staticmethod
    def monitor_for_download(download_dir, expected_extensions=None, timeout=30):
        """Simple monitor that watches for new files and waits for them to stabilize"""
        if expected_extensions is None:
            expected_extensions = ['.zip', '.mp3']
        
        logger.info(f"Simple monitor for downloads in {download_dir}")
        
        download_path = Path(download_dir)
        if not download_path.exists():
            os.makedirs(download_dir, exist_ok=True)
        
        # Record initial files
        initial_files = {}
        for file_path in download_path.iterdir():
            if file_path.is_file():
                try:
                    initial_files[file_path.name] = {
                        'path': str(file_path),
                        'size': os.path.getsize(file_path),
                        'mtime': os.path.getmtime(file_path)
                    }
                except OSError:
                    continue
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check current files
            current_files = {}
            for file_path in download_path.iterdir():
                if file_path.is_file():
                    try:
                        current_files[file_path.name] = {
                            'path': str(file_path),
                            'size': os.path.getsize(file_path),
                            'mtime': os.path.getmtime(file_path)
                        }
                    except OSError:
                        continue
            
            # Find new or modified files
            for filename, fileinfo in current_files.items():
                # Check if it's new or modified
                is_new = filename not in initial_files
                is_modified = (filename in initial_files and 
                            fileinfo['size'] != initial_files[filename]['size'])
                
                if is_new or is_modified:
                    # Check if it has a valid extension
                    has_valid_ext = any(filename.endswith(ext) for ext in expected_extensions)
                    is_temp = any(filename.endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download'])
                    
                    # We're interested in valid files or temp files that might become valid
                    if has_valid_ext or is_temp:
                        logger.debug(f"Tracking file: {filename} (size: {fileinfo['size']})")
                        
                        # If it's a valid file and not temp, check if it's stable
                        if has_valid_ext and not is_temp and fileinfo['size'] > 0:
                            # Wait a moment and check again
                            time.sleep(1)
                            try:
                                new_size = os.path.getsize(fileinfo['path'])
                                if new_size == fileinfo['size']:
                                    logger.info(f"✓ Download complete: {filename}")
                                    return fileinfo['path']
                            except OSError:
                                continue
            
            time.sleep(0.5)
        
        return None
    @staticmethod
    def simple_wait_for_download(download_dir, expected_extensions=None, timeout=30):
        """Simple, reliable method to wait for downloads"""
        if expected_extensions is None:
            expected_extensions = ['.zip', '.mp3']
        
        download_path = Path(download_dir).resolve()
        logger.info(f"Simple wait for download in {download_path}")
        
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        initial_files = {}
        for file_path in download_path.iterdir():
            if file_path.is_file():
                try:
                    initial_files[file_path.name] = {
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'mtime': file_path.stat().st_mtime
                    }
                except:
                    continue
        
        logger.info(f"Found {len(initial_files)} initial files")
        
        while time.time() - start_time < timeout:
            current_files = {}
            for file_path in download_path.iterdir():
                if file_path.is_file():
                    try:
                        current_files[file_path.name] = {
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'mtime': file_path.stat().st_mtime
                        }
                    except:
                        continue
            
            for filename, info in current_files.items():
                if filename not in initial_files:
                    has_valid_ext = any(filename.endswith(ext) for ext in expected_extensions)
                    is_temp = any(filename.endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download'])
                    
                    if has_valid_ext and not is_temp:
                        time.sleep(1)
                        try:
                            new_size = Path(info['path']).stat().st_size
                            if new_size == info['size']:
                                logger.info(f"Found stable new file: {filename} ({info['size']} bytes)")
                                return info['path']
                        except:
                            continue
                    elif is_temp:
                        logger.debug(f"Found temp file: {filename}")
                elif info['size'] > initial_files[filename]['size']:
                    logger.debug(f"File is growing: {filename} {initial_files[filename]['size']} -> {info['size']}")
            
            time.sleep(1)
        
        logger.warning(f"Timeout after {timeout} seconds")
        
        for filename, info in current_files.items():
            if filename not in initial_files:
                has_valid_ext = any(filename.endswith(ext) for ext in expected_extensions)
                is_temp = any(filename.endswith(ext) for ext in ['.part', '.crdownload', '.tmp', '.download'])
                
                if has_valid_ext and not is_temp:
                    logger.info(f"Returning new file despite timeout: {filename}")
                    return info['path']
        
        return None
    
    @staticmethod
    def overlay_audio_tag(promo_file: str, tag_file: str, output_file: str, 
                          overlap_seconds: int = 10) -> bool:
        """
        Overlay an audio tag over the last N seconds of a promo file.
        Both audio plays simultaneously during the overlap period.
        
        Args:
            promo_file: Path to the promo MP3 file
            tag_file: Path to the WAV tag file
            output_file: Path for the output MP3 file
            overlap_seconds: How many seconds to overlap (default: 10)
        
        Returns:
            True if successful, False otherwise
        """
        import subprocess
        import shlex
        
        logger.info(f"Overlaying tag over last {overlap_seconds}s of {promo_file}")
        
        if not Path(promo_file).exists():
            logger.error(f"Promo file not found: {promo_file}")
            return False
        
        if not Path(tag_file).exists():
            logger.error(f"Tag file not found: {tag_file}")
            return False
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', promo_file,
            '-i', tag_file,
            '-filter_complex',
            f'[0:a]aformat=sample_fmts=s16:channel_layouts=stereo,'
            f'adelay=0|0[promo];'
            f'[1:a]aformat=sample_fmts=s16:channel_layouts=stereo[tag];'
            f'[promo][tag]amix=inputs=2:duration=first:normalize=0[out]',
            '-map', '[out]',
            '-t', str(overlap_seconds),
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Overlay complete: {output_file}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out")
            return False
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            logger.error(f"Error overlaying audio: {e}")
            return False
    
    @staticmethod
    def overlay_promo_with_tag(promo_file: str, tag_file: str, output_file: str,
                                overlap_seconds: int = 10) -> bool:
        """
        Take the promo file, keep everything except the last N seconds,
        then append the last N seconds mixed with the tag file.
        
        Args:
            promo_file: Path to the promo MP3 file
            tag_file: Path to the WAV tag file
            output_file: Path for the output MP3 file
            overlap_seconds: How many seconds to overlap (default: 10)
        
        Returns:
            True if successful, False otherwise
        """
        import subprocess
        
        logger.info(f"Processing promo: {promo_file} with tag overlay")
        
        if not Path(promo_file).exists():
            logger.error(f"Promo file not found: {promo_file}")
            return False
        
        if not Path(tag_file).exists():
            logger.error(f"Tag file not found: {tag_file}")
            return False
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FFmpeg: promo_file = {promo_file}")
        logger.info(f"FFmpeg: tag_file = {tag_file}")
        logger.info(f"FFmpeg: output_file = {output_file}")
        
        promo_exists = Path(promo_file).exists()
        tag_exists = Path(tag_file).exists()
        logger.info(f"FFmpeg: promo exists = {promo_exists}")
        logger.info(f"FFmpeg: tag exists = {tag_exists}")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', promo_file,
            '-i', tag_file,
            '-filter_complex',
            (
                f'[0:a]aformat=sample_fmts=s16:channel_layouts=stereo[promo_fmt];'
                f'[1:a]aformat=sample_fmts=s16:channel_layouts=stereo[tag_fmt];'
                f'[promo_fmt]atrim=0:duration=(N-10),asetpts=PTS-STARTPTS[pre];'
                f'[promo_fmt]atrim=start=(N-10),asetpts=PTS-STARTPTS[ending];'
                f'[ending][tag_fmt]amix=inputs=2:duration=first:normalize=0[mixed];'
                f'[pre][mixed]concat=n=2:v=0:a=1[out]'
            ).replace('N', f'(T)'),
            '-filter_complex',
            (
                '[0:a]aformat=sample_fmts=s16:channel_layouts=stereo[promo]; '
                '[1:a]aformat=sample_fmts=s16:channel_layouts=stereo[tag]; '
                '[promo][tag]amix=inputs=2:duration=first:normalize=0[out]'
            ),
            '-map', '[out]',
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', promo_file, '-i', tag_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
        except:
            pass
        
        cmd = [
            'ffmpeg', '-y',
            '-i', promo_file,
            '-i', tag_file,
            '-filter_complex',
            f'[0:a]aformat=sample_fmts=s16:channel_layouts=stereo,fade=t=out:st=0:d=0.5[promo_out];'
            f'[1:a]aformat=sample_fmts=s16:channel_layouts=stereo[tag];'
            f'[promo_out][tag]amix=inputs=2:duration=first:normalize=0[out]',
            '-map', '[out]',
            str(output_path)
        ]
        
        try:
            logger.info(f"FFmpeg: running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Successfully created: {output_file}")
                return True
            else:
                logger.error(f"FFmpeg returncode: {result.returncode}")
                if result.stderr:
                    logger.error(f"FFmpeg stderr: {result.stderr[:1000]}")
                if result.stdout:
                    logger.info(f"FFmpeg stdout: {result.stdout[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out")
            return False
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg from https://ffmpeg.org")
            return False
        except Exception as e:
            logger.error(f"Error creating promo with tag: {e}")
            return False