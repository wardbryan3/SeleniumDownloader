"""
Standalone test to simulate download detection without needing a browser
"""
import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from sources.base import BaseDownloader

class MockBrowserManager:
    def __init__(self):
        self.driver = None
    
    def wait_for_browser_download_complete(self, timeout=60, poll_interval=1.0):
        return None

class MockConfigManager:
    def get(self, key, default=None):
        return default
    
    def get_global_features_dir(self):
        return str(Path.home() / "downloads" / "Global Features")
    
    def get_wwo_spots_dir(self):
        return str(Path.home() / "downloads" / "WWO SPOTS")
    
    def get_promos_dir(self):
        return str(Path.home() / "downloads" / "Promos")
    
    def get_tag_file(self):
        return str(Path.home() / "downloads" / "Promos" / "tag.wav")
    
    def is_test_mode(self):
        return True
    
    def ensure_folders(self):
        pass

def test_download_detection():
    print("=" * 60)
    print("DOWNLOAD DETECTION TEST")
    print("=" * 60)
    
    download_dir = tempfile.mkdtemp(prefix='test_downloads_')
    print(f"Test download directory: {download_dir}")
    
    class TestDownloader(BaseDownloader):
        def download(self, callback=None):
            return True
    
    downloader = TestDownloader(MockBrowserManager(), MockConfigManager())
    
    original_get_download_dir = downloader.get_download_dir
    downloader.get_download_dir = lambda: download_dir
    
    print("\n" + "-" * 60)
    print("TEST 1: Wait for a file that will be created in 3 seconds")
    print("-" * 60)
    
    def create_file_later():
        time.sleep(3)
        filepath = Path(download_dir) / "test_file.mp3"
        filepath.write_bytes(b'X' * 10240)
        print(f"[THREAD] Created: {filepath}")
    
    import threading
    t = threading.Thread(target=create_file_later)
    t.start()
    
    result = downloader.wait_for_download_and_get_file(timeout=10)
    
    t.join()
    
    print(f"\nResult: {result}")
    if result:
        print("TEST 1: PASSED")
    else:
        print("TEST 1: FAILED")
    
    print("\n" + "-" * 60)
    print("TEST 2: File already exists")
    print("-" * 60)
    
    existing_file = Path(download_dir) / "existing.mp3"
    existing_file.write_bytes(b'Y' * 2048)
    print(f"Created existing file: {existing_file}")
    
    result = downloader.wait_for_download_and_get_file(timeout=5)
    print(f"Result: {result}")
    if result and "existing" in result:
        print("TEST 2: PASSED")
    else:
        print("TEST 2: FAILED (should have returned existing file)")
    
    shutil.rmtree(download_dir, ignore_errors=True)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_download_detection()
