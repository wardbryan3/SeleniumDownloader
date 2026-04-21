"""
Northwest Outdoors download source
"""

import os
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

class NorthwestOutdoorsDownloader(BaseDownloader):

    """Download Northwest Outdoors files"""
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING NORTHWEST OUTDOORS DOWNLOAD ===")
        
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
            all_urls = self.config_manager.get("urls", {})
            logger.info(f"All URLs from config: {all_urls}")
            url = all_urls.get("northwest_outdoors")
            logger.info(f"URL from config: [{url}]")
            if not url or "YOUR_LINK" in url or "REMOVED" in url:
                logger.error(f"northwest_outdoors URL not configured properly in download_config.json: {url}")
                if update_callback:
                    update_callback(100, "Error: northwest_outdoors URL not configured")
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
                update_callback(60, "Processing download...")
            
            logger.info("Extracting files...")
            temp_dir = Path(tempfile.gettempdir()) / "nwo_extract"
            temp_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                logger.info(f"Extracted {len(zip_ref.namelist())} files")
            
            os.remove(downloaded_file)
            
            global_features_dir = Path(self.config_manager.get_global_features_dir())
            promos_dir = Path(self.config_manager.get_promos_dir())
            tag_file = self.config_manager.get_tag_file()
            
            global_features_dir.mkdir(parents=True, exist_ok=True)
            promos_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Processing extracted files...")
            for extracted_file in temp_dir.iterdir():
                if not extracted_file.is_file():
                    continue
                
                filename_lower = extracted_file.name.lower()
                
                if 'promo' in filename_lower:
                    logger.info(f"Processing promo file: {extracted_file.name}")
                    if update_callback:
                        update_callback(80, "Processing promo with tag...")
                    
                    output_file = promos_dir / "NWOUTPR-KORV.mp3"
                    
                    if Path(tag_file).exists():
                        from download_utils import DownloadUtilities
                        success = DownloadUtilities.overlay_promo_with_tag(
                            str(extracted_file),
                            tag_file,
                            str(output_file),
                            overlap_seconds=10
                        )
                        
                        if success:
                            logger.info(f"Promo with tag saved to {output_file}")
                        else:
                            logger.warning("Tag overlay failed, saving promo without tag")
                            shutil.copy(extracted_file, output_file)
                    else:
                        logger.warning(f"Tag file not found: {tag_file}, saving promo without tag")
                        shutil.copy(extracted_file, output_file)
                else:
                    if update_callback:
                        update_callback(90, f"Moving {extracted_file.name}...")
                    
                    output_path = global_features_dir / extracted_file.name
                    shutil.copy(extracted_file, output_path)
                    logger.info(f"Copied {extracted_file.name} to {output_path}")
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if update_callback:
                update_callback(100, "Complete")
            
            logger.info("=== NORTHWEST OUTDOORS DOWNLOAD COMPLETE ===")
            
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in Northwest Outdoors download: {e}")
            import traceback
            traceback.print_exc()
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False
