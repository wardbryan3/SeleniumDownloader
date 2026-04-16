"""
Melinda Myers download source
"""

import os
import time
import logging
import shutil
from pathlib import Path

from selenium.webdriver.common.by import By

from .base import BaseDownloader

logger = logging.getLogger(__name__)

class MelindaMyersDownloader(BaseDownloader):
    """Download Melinda Myers audio files"""
    
    def download(self, update_callback=None) -> bool:
        logger.info("Starting Melinda Myers download")
        
        if not self.browser_manager.start_browser():
            return False
        
        try:
            output_dir = Path(self.config_manager.get_global_features_dir())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            driver = self.browser_manager.get_driver()
            if not driver:
                return False
            
            for i, day_name in [(0, "Monday"), (2, "Wednesday"), (4, "Friday")]:
                if update_callback:
                    update_callback(0, f"Downloading {day_name}...")
                
                driver.get("https://www.melindamyers.com/media/")
                time.sleep(2)
                
                try:
                    link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Audio_Tips_3x")
                    link_element.click()
                    time.sleep(2)
                    
                    weekday = self.find_coming_weekday(i)
                    download_link = driver.find_element(By.PARTIAL_LINK_TEXT, weekday)
                    download_link.click()
                    
                    logger.info(f"Initiated download for {day_name}")
                    
                    downloaded_file = self.wait_for_download_and_get_file(timeout=15)
                    
                    if downloaded_file:
                        day_map = {0: "MMMON.mp3", 2: "MMWED.mp3", 4: "MMFRI.mp3"}
                        new_name = day_map.get(i)
                        if new_name:
                            new_path = output_dir / new_name
                            if Path(downloaded_file).resolve() != new_path.resolve():
                                shutil.move(downloaded_file, new_path)
                            logger.info(f"Saved {day_name} as {new_name}")
                    else:
                        logger.warning(f"No file downloaded for {day_name}")
                
                except Exception as e:
                    logger.error(f"Error downloading {day_name}: {e}")
                    continue
            
            for i, day_name in [(1, "Tuesday"), (3, "Thursday")]:
                if update_callback:
                    update_callback(0, f"Downloading {day_name}...")
                
                driver.get("https://www.melindamyers.com/media/")
                time.sleep(2)
                
                try:
                    link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Audio_Tips_5x")
                    link_element.click()
                    time.sleep(2)
                    
                    weekday = self.find_coming_weekday(i)
                    download_link = driver.find_element(By.PARTIAL_LINK_TEXT, weekday)
                    download_link.click()
                    
                    logger.info(f"Initiated download for {day_name}")
                    
                    downloaded_file = self.wait_for_download_and_get_file(timeout=60)
                    
                    if downloaded_file:
                        day_map = {1: "MMTUE.mp3", 3: "MMTHU.mp3"}
                        new_name = day_map.get(i)
                        if new_name:
                            new_path = output_dir / new_name
                            if Path(downloaded_file).resolve() != new_path.resolve():
                                shutil.move(downloaded_file, new_path)
                            logger.info(f"Saved {day_name} as {new_name}")
                    else:
                        logger.warning(f"No file downloaded for {day_name}")
                
                except Exception as e:
                    logger.error(f"Error downloading {day_name}: {e}")
                    continue
            
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            
            logger.info("Melinda Myers download completed")
            return True
            
        except Exception as e:
            logger.error(f"Error in Melinda Myers download: {e}")
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False
