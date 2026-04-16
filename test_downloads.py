"""
Test utilities for simulating downloads and testing detection logic
"""

import os
import time
import tempfile
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DownloadSimulator:
    """Simulate download scenarios for testing"""
    
    @staticmethod
    def create_test_file(directory: str, filename: str, size_kb: int = 100, delay_seconds: float = 0):
        """Create a test file in the specified directory"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = Path(directory) / filename
        
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        
        with open(filepath, 'wb') as f:
            f.write(b'X' * (size_kb * 1024))
        
        logger.info(f"Created test file: {filepath} ({size_kb}KB)")
        return str(filepath)
    
    @staticmethod
    def create_downloading_file(directory: str, filename: str, total_size_kb: int = 100, chunk_delay: float = 0.1):
        """Simulate a file being downloaded with growing size"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = Path(directory) / filename
        
        chunk_size = 1024
        chunks = (total_size_kb * 1024) // chunk_size
        
        with open(filepath, 'wb') as f:
            for i in range(chunks):
                f.write(b'X' * chunk_size)
                f.flush()
                time.sleep(chunk_delay)
        
        logger.info(f"Completed simulated download: {filepath}")
        return str(filepath)
    
    @staticmethod
    def simulate_incremental_download(directory: str, filename: str, total_size_kb: int = 100):
        """Simulate download by creating file incrementally"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = Path(directory) / filename
        
        chunk_size = 1024
        chunks = (total_size_kb * 1024) // chunk_size
        
        with open(filepath, 'wb') as f:
            for i in range(chunks):
                f.write(b'X' * chunk_size)
                time.sleep(0.05)
        
        return str(filepath)


def test_download_detection():
    """Test the download detection logic"""
    from download_utils import DownloadUtilities
    from sources.base import BaseDownloader
    
    print("=" * 50)
    print("Testing Download Detection")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp(prefix='download_test_')
    print(f"\nTest directory: {test_dir}")
    
    print("\n1. Testing file creation and detection...")
    
    file1 = DownloadSimulator.create_test_file(test_dir, "test1.mp3", size_kb=10)
    time.sleep(0.5)
    
    print("\n2. Testing simple_wait_for_download...")
    result = DownloadUtilities.simple_wait_for_download(
        test_dir,
        expected_extensions=['.mp3'],
        timeout=5
    )
    print(f"Result: {result}")
    
    print("\n3. Testing monitor_for_download...")
    test_dir2 = tempfile.mkdtemp(prefix='download_monitor_test_')
    
    def create_file_in_background():
        time.sleep(1)
        DownloadSimulator.create_test_file(test_dir2, "test2.mp3", size_kb=20)
    
    import threading
    t = threading.Thread(target=create_file_in_background)
    t.start()
    
    result = DownloadUtilities.monitor_for_download(
        test_dir2,
        expected_extensions=['.mp3'],
        timeout=10
    )
    t.join()
    print(f"Result: {result}")
    
    print("\n4. Testing find_latest_file...")
    DownloadSimulator.create_test_file(test_dir, "test3.mp3", size_kb=15)
    time.sleep(1)
    result = DownloadUtilities.find_latest_file(test_dir, extension='.mp3')
    print(f"Result: {result}")
    
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree(test_dir2, ignore_errors=True)
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


def test_config_paths():
    """Test configuration paths"""
    from config import ConfigManager
    
    print("=" * 50)
    print("Testing Configuration Paths")
    print("=" * 50)
    
    config = ConfigManager()
    
    print(f"\nTest mode: {config.is_test_mode()}")
    print(f"Output base: {config.get_output_base_dir()}")
    print(f"Global Features: {config.get_global_features_dir()}")
    print(f"WWO SPOTS: {config.get_wwo_spots_dir()}")
    print(f"Promos: {config.get_promos_dir()}")
    print(f"Tag file: {config.get_tag_file()}")
    
    config.ensure_folders()
    
    for folder in ['Global Features', 'WWO SPOTS', 'Promos']:
        path = config.get_global_features_dir().replace('Global Features', folder)
        if Path(path).exists():
            print(f"✓ {folder} folder exists")
        else:
            print(f"✗ {folder} folder missing")
    
    print("\n" + "=" * 50)


def test_browser_manager():
    """Test browser manager initialization"""
    from browser_manager import BrowserManager
    from config import ConfigManager
    
    print("=" * 50)
    print("Testing Browser Manager")
    print("=" * 50)
    
    config = ConfigManager()
    bm = BrowserManager(config)
    
    print(f"\nTemp download dir: {bm._get_temp_download_dir()}")
    print(f"Browser open: {bm.is_browser_open()}")
    
    print("\nNote: Browser start requires Firefox installed")
    print("=" * 50)


def test_all_sources():
    """Test creating all downloader instances"""
    from sources import create_downloader
    from browser_manager import BrowserManager
    from config import ConfigManager, DOWNLOAD_SOURCES
    
    print("=" * 50)
    print("Testing All Download Sources")
    print("=" * 50)
    
    config = ConfigManager()
    bm = BrowserManager(config)
    
    print(f"\nAvailable sources: {list(DOWNLOAD_SOURCES.keys())}")
    
    for name in DOWNLOAD_SOURCES.keys():
        try:
            d = create_downloader(name, bm, config)
            print(f"✓ {name}: OK")
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    print("\n" + "=" * 50)


def run_all_tests():
    """Run all tests"""
    print("\n" + "#" * 50)
    print("# AUDIO DOWNLOAD MANAGER - TEST SUITE")
    print("#" * 50 + "\n")
    
    test_config_paths()
    test_all_sources()
    test_download_detection()
    test_browser_manager()
    
    print("\n" + "#" * 50)
    print("# ALL TESTS COMPLETED")
    print("#" * 50 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    run_all_tests()
