"""
Westwood One download source
"""

import os
import zipfile
import time
import logging
import tempfile
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseDownloader

logger = logging.getLogger(__name__)

class WestwoodOneDownloader(BaseDownloader):
    """Download Westwood One files"""
    
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING WESTWOOD ONE DOWNLOAD ===")
        
        try:
            logger.info("Starting browser...")
            if not self.browser_manager.start_browser():
                logger.error("Failed to start browser")
                return False
            
            driver = self.browser_manager.get_driver()
            if not driver:
                logger.error("Failed to get driver")
                return False
            
            logger.info("Browser started successfully")
            
            email = self.config_manager.get("email", "")
            password = self.config_manager.get("password", "")
            
            if not email or not password:
                logger.error("Email and password required for Westwood One")
                if update_callback:
                    update_callback(100, "Error: Email/password not configured")
                return False
            
            logger.info(f"Using email: {email}")
            
            if update_callback:
                update_callback(5, "Accessing Westwood One...")
            
            # Step 1: Navigate to Westwood One
            logger.info("Navigating to Westwood One...")
            driver.get("https://cdn.westwoodone.com/packages")
            time.sleep(5)
            logger.info(f"Page title: {driver.title}")
            logger.info(f"Current URL: {driver.current_url}")
            
            # Take screenshot for debugging
            try:
                driver.save_screenshot("/tmp/wwo_page.png")
                logger.info("Screenshot saved to /tmp/wwo_page.png")
            except Exception as e:
                logger.info(f"Could not save screenshot: {e}")
            
            if update_callback:
                update_callback(20, "Requesting magic link...")
            
            # Step 2: Enter email
            logger.info("Looking for email field...")
            
            # Try multiple possible selectors for the email field
            email_field = None
            selectors = [
                (By.ID, "passwordless_email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='email']"),
                (By.XPATH, "//input[contains(@placeholder, 'email')]"),
                (By.XPATH, "//input[contains(@id, 'email')]"),
            ]
            
            for by, value in selectors:
                try:
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((by, value))
                    )
                    if email_field:
                        logger.info(f"Found email field with {by}: {value}")
                        break
                except:
                    logger.info(f"Could not find email field with {by}: {value}")
            
            if not email_field:
                logger.error("Could not find email field with any selector")
                logger.error(f"Page title: {driver.title}")
                logger.error(f"Page URL: {driver.current_url}")
                if update_callback:
                    update_callback(100, f"Error: Page not loading correctly")
                return False
            
            email_field.send_keys(email)
            logger.info("Email entered")
            
            logger.info("Looking for send button...")
            try:
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div/div[2]/form/div[2]/div/button'))
                )
                time.sleep(1)
                send_button.click()
                logger.info("Magic link requested, waiting 60 seconds for email to arrive...")
            except Exception as e:
                logger.error(f"Could not find or click send button: {e}")
                if update_callback:
                    update_callback(100, f"Error: Could not click send button")
                return False
            
            time.sleep(60)
            
            if update_callback:
                update_callback(30, "Accessing email...")
            
            # Step 3: Login to email
            logger.info("Navigating to email...")
            driver.get("https://webmail8.userservices.net/")
            time.sleep(3)
            
            logger.info("Logging into email...")
            
            # Try multiple selectors for login fields
            try:
                email_login = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, 'rcmloginuser'))
                )
                logger.info("Found email login field")
            except Exception as e:
                logger.error(f"Could not find email login field: {e}")
                # Try alternative selectors
                try:
                    email_login = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.NAME, 'user'))
                    )
                    logger.info("Found email login field by name")
                except:
                    email_login = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='user']"))
                    )
                    logger.info("Found email login field by CSS")
            
            email_password = driver.find_element(By.ID, 'rcmloginpwd')
            email_login.send_keys(email)
            email_password.send_keys(password)
            logger.info("Credentials entered")
            
            # Try multiple selectors for login button
            login_button = None
            button_selectors = [
                (By.XPATH, '/html/body/div[1]/div/div[2]/form/div[5]/button'),
                (By.XPATH, '//button[@type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Login")]'),
                (By.XPATH, '//button[contains(text(), "Sign in")]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
            ]
            
            for by, value in button_selectors:
                try:
                    login_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((by, value))
                    )
                    logger.info(f"Found login button with {by}: {value}")
                    break
                except:
                    logger.info(f"Could not find login button with {by}: {value}")
            
            if not login_button:
                logger.error("Could not find login button")
                if update_callback:
                    update_callback(100, "Error: Could not find login button")
                return False
            
            login_button.click()
            logger.info("Email login submitted, waiting for inbox...")
            time.sleep(10)
            
            if update_callback:
                update_callback(40, "Finding magic link...")
            
            # Step 4: Find magic link email
            logger.info("Waiting for email inbox to load...")
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "messagelist"))
            )
            
            magic_link_emails = driver.find_elements(
                By.XPATH, 
                "//tr[contains(@class, 'message')]//a[contains(., 'Your magic link')]"
            )
            
            if not magic_link_emails:
                logger.error("No magic link emails found")
                return False
            
            # Click most recent email
            magic_link_emails[0].click()
            time.sleep(5)
            
            if update_callback:
                update_callback(50, "Extracting magic link...")
            
            # Step 5: Extract magic link
            magic_link = None
            
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        login_links = driver.find_elements(
                            By.XPATH, 
                            "//a[contains(text(), 'Login to CDN')]"
                        )
                        if login_links:
                            magic_link = login_links[0].get_attribute('href')
                            break
                    finally:
                        driver.switch_to.default_content()
            except Exception as e:
                logger.error(f"Error extracting magic link: {e}")
            
            if not magic_link:
                logger.error("Could not find magic link in email")
                return False
            
            if update_callback:
                update_callback(60, "Authenticating...")
            
            # Step 6: Use magic link
            driver.get(magic_link)
            time.sleep(3)
            
            if update_callback:
                update_callback(70, "Finding package...")
            
            # Step 7: Find and click package
            time.sleep(2)
            
            # Try multiple selectors for the package
            package_selectors = [
                "//a[contains(text(), 'Country Nights Live w Bev Rainey ROS_A')]",
                "//*[contains(text(), 'Country Nights Live w Bev Rainey ROS_A')]",
                "//a[contains(., 'Country Nights Live')]",
                "//*[contains(., 'Country Nights Live')]"
            ]
            
            package_link = None
            for selector in package_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            package_link = element
                            break
                    if package_link:
                        break
                except:
                    continue
            
            if not package_link:
                logger.error("Could not find package link")
                return False
            
            package_link.click()
            time.sleep(3)
            
            if update_callback:
                update_callback(80, "Downloading files...")
            
            # Step 8: Click download button using WebDriverWait
            download_button = None
            for xpath in [
                "/html/body/main/div[2]/div/div/div/div/div/table/tbody/tr[1]/td/a",
                "//a[contains(@href, 'download')]",
                "//a[contains(text(), 'Download')]",
                "//a[contains(@class, 'download')]"
            ]:
                try:
                    logger.info(f"Trying XPath: {xpath}")
                    download_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"Found download button with XPath: {xpath}")
                    break
                except:
                    logger.info(f"XPath not found: {xpath}")
            
            if not download_button:
                logger.error("Could not find download button")
                return False
            
            time.sleep(2)
            logger.info("Clicking download button...")
            download_button.click()
            logger.info("Download button clicked")
            time.sleep(5)
            
            logger.info("Download initiated")
            
            if update_callback:
                update_callback(85, "Waiting for download...")
            
            # Wait for download
            downloaded_file = self.wait_for_download_and_get_file(timeout=300)
            
            if not downloaded_file:
                logger.error("No downloaded file found")
                return False
            
            if update_callback:
                update_callback(90, "Extracting files...")
            
            # Step 9: Extract ZIP file
            output_dir = Path(self.config_manager.get_wwo_spots_dir())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            temp_dir = Path(tempfile.gettempdir()) / "wwo_extract"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                logger.info(f"Extracted {len(zip_ref.namelist())} files")
            except zipfile.BadZipFile:
                logger.error(f"Invalid ZIP file: {downloaded_file}")
                return False
            
            import shutil
            for extracted_file in temp_dir.iterdir():
                if extracted_file.is_file():
                    shutil.copy(extracted_file, output_dir / extracted_file.name)
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Cleanup
            os.remove(downloaded_file)
            
            if update_callback:
                update_callback(100, "Complete")
            
            # Auto-close browser if enabled
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            
            logger.info("Westwood One download completed")
            return True
            
        except Exception as e:
            logger.error(f"Error in Westwood One download: {e}")
            import traceback
            traceback.print_exc()
            
            # Auto-close browser even on error if enabled
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False