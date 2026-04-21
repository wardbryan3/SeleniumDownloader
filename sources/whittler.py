"""
Whittler download source
"""

import os
import glob
import zipfile
import time
import logging
import shutil
import tempfile
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseDownloader

logger = logging.getLogger(__name__)

class WhittlerDownloader(BaseDownloader):
    """Download Whittler files"""
    
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING WHITTLER DOWNLOAD ===")
        
        if not self.browser_manager.start_browser():
            logger.error("Failed to start browser")
            return False
        
        try:
            driver = self.browser_manager.get_driver()
            if not driver:
                logger.error("Failed to get driver")
                return False
            
            if update_callback:
                update_callback(5, "Accessing download page...")
            
            logger.info("Navigating to Dropbox URL...")
            url = self.config_manager.get("urls", {}).get("whittler")
            if not url or "YOUR_LINK" in url:
                logger.error("whittler URL not configured in download_config.json")
                if update_callback:
                    update_callback(100, "Error: whittler URL not configured")
                return False
            driver.get(url)
            
            logger.info("Waiting for page to load...")
            time.sleep(10)
            
            logger.info("Waiting for download button to be clickable...")
            wait = WebDriverWait(driver, 30)
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/span/span/div/span/div/div/div/div/div[2]/div/div[1]/span/div/div[2]/span[1]/button/span/span/span"))
            )
            time.sleep(2)
            logger.info("Found download button, clicking...")
            download_button.click()
            logger.info("Download button clicked")
            time.sleep(3)
            
            logger.info("Waiting for confirm popup...")
            if update_callback:
                update_callback(30, "Confirming download...")
            
            confirm_button = None
            for xpath in [
                "//button[contains(., 'continue with download')]",
                "/html/body/div[9]/div/div/div/div[3]/div/span/button/span"
            ]:
                try:
                    confirm_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"Found confirm button with XPath: {xpath}")
                    break
                except:
                    logger.info(f"XPath not found: {xpath}")
            
            if confirm_button:
                time.sleep(1)
                logger.info("Clicking confirm button...")
                confirm_button.click()
                logger.info("Confirm button clicked")
                time.sleep(2)
            else:
                logger.warning("No confirm button found")
                time.sleep(3)
            
            logger.info("Polling for download file...")
            if update_callback:
                update_callback(40, "Waiting for download...")
            
            downloaded_file = self.wait_for_download_and_get_file(timeout=300)
            
            if not downloaded_file:
                logger.error("No downloaded file found after waiting")
                if update_callback:
                    update_callback(100, "Download failed - no file found")
                return False
            
            logger.info(f"Download detected: {downloaded_file}")
            
            if update_callback:
                update_callback(60, "Extracting files...")
            
            logger.info("Extracting files...")
            temp_dir = Path(tempfile.gettempdir()) / "whittler_extract"
            temp_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                logger.info(f"Extracted {len(zip_ref.namelist())} files")
            
            os.remove(downloaded_file)
            
            if update_callback:
                update_callback(80, "Moving files to Global Features...")
            
            output_dir = Path(self.config_manager.get_global_features_dir())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            part_mapping = {
                "Part A": "Whittler1",
                "Part B": "Whittler2",
                "Part C": "Whittler3",
                "Part D": "Whittler4"
            }
            
            logger.info("Renaming and copying files...")
            for old_part, new_name in part_mapping.items():
                pattern = temp_dir / f"*{old_part}*.mp3"
                files = list(temp_dir.glob(f"*{old_part}*.mp3"))
                
                for file_path in files:
                    new_filename = f"{new_name}.mp3"
                    new_path = output_dir / new_filename
                    shutil.copy(file_path, new_path)
                    logger.info(f"Copied: {file_path.name} -> {new_filename}")
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if update_callback:
                update_callback(100, "Complete")
            
            logger.info("=== WHITTLER DOWNLOAD COMPLETE ===")
            
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in Whittler download: {e}")
            import traceback
            traceback.print_exc()
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False
