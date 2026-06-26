"""
Clear Out West download source
"""

import time
import re
import logging
import shutil
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base import BaseDownloader

logger = logging.getLogger(__name__)

class ClearOutWestDownloader(BaseDownloader):
    """Download Clear Out West files"""
    
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING CLEAR OUT WEST DOWNLOAD ===")
        
        if not self.browser_manager.start_browser():
            logger.error("Failed to start browser")
            return False
        
        try:
            driver = self.browser_manager.get_driver()
            if not driver:
                logger.error("Failed to get driver")
                return False
            
            password = self.config_manager.get("cow_password")
            if not password:
                logger.error("cow_password not configured in download_config.json")
                if update_callback:
                    update_callback(100, "Error: cow_password not configured")
                return False
            
            if update_callback:
                update_callback(5, "Accessing website...")
            
            logger.info("Navigating to Clear Out West...")
            driver.get("https://www.clearoutwest.com/download-radio-stations-only.html")
            
            logger.info("Waiting for page to load...")
            time.sleep(5)
            
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            if update_callback:
                update_callback(15, "Checking for login...")
            
            if self._handle_login(driver, password):
                logger.info("Logged in successfully")
                time.sleep(3)
                if update_callback:
                    update_callback(30, "Logged in, finding downloads...")
            else:
                logger.info("No login required")
                if update_callback:
                    update_callback(30, "No login needed, finding downloads...")
            
            time.sleep(2)
            
            if update_callback:
                update_callback(40, "Looking for download link...")
            
            logger.info("Looking for all download links...")
            all_hrefs = []
            page_url = driver.current_url
            
            download_selectors = [
                "//a[contains(@href, '.mp3')]",
                "//a[contains(@href, '.zip')]",
            ]
            
            for selector in download_selectors:
                try:
                    links = driver.find_elements(By.XPATH, selector)
                    for link in links:
                        if link.is_displayed() and link.is_enabled():
                            href = link.get_attribute('href')
                            if href and (href.endswith('.mp3') or href.endswith('.zip')):
                                logger.info(f"Found download link: {href[:50]}...")
                                if href not in all_hrefs:
                                    all_hrefs.append(href)
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not all_hrefs:
                logger.error("No download links found")
                if update_callback:
                    update_callback(100, "Download failed - no links found")
                return False
            
            logger.info(f"Found {len(all_hrefs)} download links")
            
            output_dir = Path(self.config_manager.get_global_features_dir())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for index, href in enumerate(all_hrefs, start=1):
                if update_callback:
                    update_callback(20 * index, f"Downloading {index}/{len(all_hrefs)}...")
                
                logger.info(f"Downloading file {index}/{len(all_hrefs)}...")
                time.sleep(2)
                
                filename = href.split('/')[-1]
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(1)
                
                link_xpath = f"//a[contains(@href, '{filename}')]"
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, link_xpath))
                )
                link = driver.find_element(By.XPATH, link_xpath)
                driver.execute_script("arguments[0].click();", link)
                logger.info(f"Clicked link {index}")
                
                downloaded_file = self.wait_for_download_and_get_file(timeout=90)
                
                if not downloaded_file:
                    logger.error(f"Download failed for file {index}")
                    if update_callback:
                        update_callback(100, f"Download failed - file {index}")
                    return False
                
                logger.info(f"Download detected: {downloaded_file}")
                
                ext = Path(downloaded_file).suffix
                match = re.search(r'track(\d+)', filename)
                if match:
                    track_num = match.group(1).lstrip('0') or '0'
                    if track_num == '5':
                        new_name = f"COWPROMO{ext}"
                    else:
                        new_name = f"COW{track_num}{ext}"
                else:
                    new_name = f"COW{index}{ext}"
                output_path = output_dir / new_name
                
                if Path(downloaded_file).resolve() != output_path.resolve():
                    shutil.move(downloaded_file, output_path)
                    logger.info(f"Moved and renamed to {new_name}")
                
                time.sleep(2)
                
                if index < len(all_hrefs):
                    logger.info("Navigating back to download page...")
                    driver.get(page_url)
                    time.sleep(3)
            
            if update_callback:
                update_callback(100, "Complete")
            
            logger.info("=== CLEAR OUT WEST DOWNLOAD COMPLETE ===")
            
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in Clear Out West download: {e}")
            import traceback
            traceback.print_exc()
            
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False
    
    def _handle_login(self, driver, password: str) -> bool:
        """Handle login if required. Returns True if logged in."""
        logger.info("Checking for login form...")
        
        login_selectors = [
            "//input[@type='password']",
            "//form[contains(@action, 'login')]",
            "//input[contains(@name, 'password')]",
        ]
        
        for selector in login_selectors:
            try:
                password_fields = driver.find_elements(By.XPATH, selector)
                if password_fields:
                    logger.info("Login page detected, entering password...")
                    
                    password_field = driver.find_element(By.XPATH, selector)
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    time.sleep(1)
                    
                    submit_button = None
                    submit_selectors = [
                        "//button[@type='submit']",
                        "//input[@type='submit']",
                        "//button[contains(text(), 'Submit')]",
                        "//button[contains(text(), 'Download')]",
                        "//form//button",
                    ]
                    
                    for btn_selector in submit_selectors:
                        buttons = driver.find_elements(By.XPATH, btn_selector)
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                submit_button = btn
                                break
                        if submit_button:
                            break
                    
                    if submit_button:
                        logger.info("Submitting login...")
                        driver.execute_script("arguments[0].click();", submit_button)
                        time.sleep(3)
                        logger.info("Login submitted")
                        return True
                    else:
                        logger.info("Submitting form via enter key...")
                        driver.find_element(By.TAG_NAME, "form").submit()
                        time.sleep(3)
                        return True
                        
            except Exception as e:
                logger.debug(f"Login selector {selector} not found: {e}")
                continue
        
        logger.info("No login form found")
        return False
