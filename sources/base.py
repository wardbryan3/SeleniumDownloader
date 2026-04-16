# [file name]: base.py
"""
Base class for download sources
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

class BaseDownloader(ABC):
    """Base class for all download sources"""
    
    def __init__(self, browser_manager, config_manager):
        self.browser_manager = browser_manager
        self.config_manager = config_manager
    
    @abstractmethod
    def download(self, update_callback=None) -> bool:
        """Download from this source"""
        pass
    
    def handle_dropbox_popup(self, driver):
        """Handle Dropbox sign-in popup if it appears"""
        try:
            time.sleep(1)
            
            popup_selectors = [
                "//a[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Continue')]",
                "//a[contains(text(), 'Sign in')]",
                "//button[contains(text(), 'Download')]",
            ]
            
            for selector in popup_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            logger.info(f"Clicking popup button: {selector}")
                            driver.execute_script("arguments[0].click();", elem)
                            time.sleep(2)
                            return
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"No popup to handle: {e}")
    
    def find_coming_weekday(self, weekday: int) -> str:
        """Find the date string for the coming weekday"""
        today = datetime.now().date()
        days_until_weekday = (weekday - today.weekday() + 7) % 7 
        
        if days_until_weekday == 0 and today.weekday() == 1:
            days_until_weekday = 7
        
        coming_weekday = today + timedelta(days=days_until_weekday)
        return coming_weekday.strftime('%m%d%y')
    
    def get_download_dir(self) -> str:
        """Get the dedicated browser download directory"""
        download_dir = self.config_manager.get_browser_download_dir()
        logger.info(f"Download directory: {download_dir}")
        return download_dir
    
    def should_auto_close_browser(self) -> bool:
        """Check if browser should auto-close"""
        return self.config_manager.get("auto_close_browser", True)
    
    def wait_for_download_and_get_file(self, timeout: int = 30):
        """
        Wait for download to complete and return the file path.
        Uses browser-based detection combined with filesystem monitoring.
        Only accepts audio/document/archive files.
        """
        import time
        download_dir = Path(self.get_download_dir())
        logger.info(f"=== WAIT FOR DOWNLOAD START ===")
        logger.info(f"Download directory: {download_dir}")
        logger.info(f"Timeout: {timeout}s")
        
        allowed_extensions = {'.zip', '.mp3', '.wav', '.pdf', '.rar', '.7z', '.tar', '.gz'}
        excluded_extensions = {'.part', '.crdownload', '.tmp', '.download', '.xpi', '.so', '.lock'}
        excluded_prefixes = {'.fea', '.X'}
        
        start_time = time.time()
        known_files = {}
        for f in download_dir.iterdir():
            if f.is_file():
                try:
                    known_files[f.name] = f.stat().st_size
                except:
                    known_files[f.name] = 0
        logger.info(f"Initial files in directory ({len(known_files)}): {list(known_files.keys())}")
        
        from download_utils import DownloadUtilities
        
        iteration = 0
        while time.time() - start_time < timeout:
            iteration += 1
            elapsed = time.time() - start_time
            
            if iteration % 5 == 0:
                all_files = [f for f in download_dir.iterdir() if f.is_file()]
                logger.info(f"[{elapsed:.1f}s] Directory contents: {[f.name for f in all_files]}")
            
            browser_result = self.browser_manager.wait_for_browser_download_complete(
                timeout=1,
                poll_interval=0.3
            )
            if browser_result:
                logger.info(f"Browser confirmed download: {Path(browser_result).name}")
                logger.info(f"=== WAIT FOR DOWNLOAD END (SUCCESS) ===")
                return browser_result
            
            for f in download_dir.iterdir():
                if f.is_file():
                    try:
                        has_excluded = any(f.name.endswith(ext) for ext in excluded_extensions)
                        has_excluded_prefix = any(f.name.startswith(prefix) for prefix in excluded_prefixes)
                        if has_excluded or has_excluded_prefix:
                            continue
                        
                        current_size = f.stat().st_size
                        prev_size = known_files.get(f.name, 0)
                        
                        if f.name not in known_files:
                            has_allowed = any(f.name.lower().endswith(ext) for ext in allowed_extensions)
                            if has_allowed:
                                logger.info(f"[{elapsed:.1f}s] NEW DOWNLOAD: {f.name} ({current_size} bytes)")
                                
                                if current_size > 0:
                                    time.sleep(1)
                                    try:
                                        new_size = f.stat().st_size
                                        if new_size == current_size:
                                            known_files[f.name] = current_size
                                            logger.info(f"[{elapsed:.1f}s] FILE STABLE: {f.name} ({current_size} bytes) - ACCEPTING")
                                            logger.info(f"=== WAIT FOR DOWNLOAD END (NEW FILE) ===")
                                            return str(f)
                                        else:
                                            logger.info(f"[{elapsed:.1f}s] FILE STILL GROWING: {f.name} ({current_size} -> {new_size})")
                                            known_files[f.name] = new_size
                                    except:
                                        pass
                        elif current_size != prev_size and prev_size > 0:
                            if any(f.name.lower().endswith(ext) for ext in allowed_extensions):
                                logger.info(f"[{elapsed:.1f}s] FILE GROWING: {f.name} ({prev_size} -> {current_size} bytes)")
                                known_files[f.name] = current_size
                    except Exception as e:
                        logger.debug(f"Error checking file {f.name}: {e}")
            
            time.sleep(0.3)
        
        logger.warning(f"=== DOWNLOAD TIMEOUT after {timeout}s ===")
        all_files = [f for f in download_dir.iterdir() if f.is_file()]
        logger.info(f"Final directory contents: {[f.name for f in all_files]}")
        
        fallback = DownloadUtilities.find_latest_file(str(download_dir), wait_time=1)
        if fallback:
            result_path = Path(fallback)
            has_excluded = any(result_path.name.endswith(ext) for ext in excluded_extensions)
            has_allowed = any(result_path.name.lower().endswith(ext) for ext in allowed_extensions)
            if has_excluded or not has_allowed:
                logger.info(f"Fallback file not a valid download, ignoring: {result_path.name}")
                fallback = None
            else:
                logger.info(f"Fallback found: {result_path.name}")
        
        logger.info(f"=== WAIT FOR DOWNLOAD END {'(' + Path(fallback).name + ')' if fallback else '(FAILED)'} ===")
        return fallback
