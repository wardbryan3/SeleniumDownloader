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


def _download_nwo_zip(downloader, update_callback=None):
    """Download and extract the Northwest Outdoors ZIP from Dropbox.

    Args:
        downloader: A BaseDownloader subclass instance.
        update_callback: Optional progress callback.

    Returns:
        Path to temp directory with extracted files, or None on failure.
    """
    if not downloader.browser_manager.start_browser():
        logger.error("Failed to start browser")
        return None

    driver = downloader.browser_manager.get_driver()
    if not driver:
        logger.error("Failed to get driver")
        return None

    if update_callback:
        update_callback(5, "Accessing download page...")

    logger.info("Navigating to Dropbox URL...")
    all_urls = downloader.config_manager.get("urls", {})
    url = all_urls.get("northwest_outdoors")
    if not url or "YOUR_LINK" in url or "REMOVED" in url:
        logger.error(f"northwest_outdoors URL not configured properly: {url}")
        if update_callback:
            update_callback(100, "Error: northwest_outdoors URL not configured")
        return None
    driver.get(url)

    logger.info("Waiting for page to load...")
    time.sleep(10)

    logger.info("Waiting for download button to be clickable...")
    wait = WebDriverWait(driver, 30)
    download_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/span/span/div/span/div/div/div/div/div[2]/div/div[1]/span/div/div[2]/span[1]/button/span/span/span"))
    )
    time.sleep(2)
    download_button.click()
    time.sleep(3)

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
            break
        except Exception:
            continue

    if confirm_button:
        time.sleep(1)
        confirm_button.click()
        time.sleep(2)
    else:
        logger.warning("No confirm button found")
        time.sleep(3)

    if update_callback:
        update_callback(40, "Waiting for download...")

    downloaded_file = downloader.wait_for_download_and_get_file(timeout=300)

    if not downloaded_file:
        logger.error("No downloaded file found after waiting")
        if update_callback:
            update_callback(100, "Download failed - no file found")
        return None

    if update_callback:
        update_callback(60, "Processing download...")

    logger.info("Extracting files...")
    temp_dir = Path(tempfile.mkdtemp(prefix="nwo_extract_"))
    with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        logger.info(f"Extracted {len(zip_ref.namelist())} files")

    os.remove(downloaded_file)

    return temp_dir


class NorthwestOutdoorsDownloader(BaseDownloader):
    """Download Northwest Outdoors non-promo files (Global Features)"""
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING NORTHWEST OUTDOORS DOWNLOAD ===")

        temp_dir = _download_nwo_zip(self, update_callback)
        if temp_dir is None:
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False

        try:
            global_features_dir = Path(self.config_manager.get_global_features_dir())
            global_features_dir.mkdir(parents=True, exist_ok=True)

            found_files = False
            for extracted_file in temp_dir.iterdir():
                if not extracted_file.is_file():
                    continue

                if 'promo' in extracted_file.name.lower():
                    logger.info(f"Skipping promo file: {extracted_file.name}")
                    continue

                found_files = True
                if update_callback:
                    update_callback(90, f"Moving {extracted_file.name}...")

                output_path = global_features_dir / extracted_file.name
                shutil.copy(extracted_file, output_path)
                logger.info(f"Copied {extracted_file.name} to {output_path}")

            shutil.rmtree(temp_dir, ignore_errors=True)

            if update_callback:
                update_callback(100, "Complete")

            logger.info("=== NORTHWEST OUTDOORS DOWNLOAD COMPLETE ===")

            if not found_files:
                logger.warning("No non-promo files found in download")
                return False

            return True

        except Exception as e:
            logger.error(f"Error processing Northwest Outdoors download: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()


class NorthwestOutdoorsPromoDownloader(BaseDownloader):
    """Download only promo files from Northwest Outdoors"""
    def download(self, update_callback=None) -> bool:
        logger.info("=== STARTING NORTHWEST OUTDOORS PROMO DOWNLOAD ===")

        temp_dir = _download_nwo_zip(self, update_callback)
        if temp_dir is None:
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
            return False

        try:
            promos_dir = Path(self.config_manager.get_promos_dir())
            tag_file = self.config_manager.get_tag_file()

            promos_dir.mkdir(parents=True, exist_ok=True)

            found_promo = False
            for extracted_file in temp_dir.iterdir():
                if not extracted_file.is_file():
                    continue

                if 'promo' not in extracted_file.name.lower():
                    continue

                found_promo = True
                logger.info(f"Processing promo file: {extracted_file.name}")
                if update_callback:
                    update_callback(80, "Processing promo with tag...")

                output_file = promos_dir / extracted_file.name

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

            shutil.rmtree(temp_dir, ignore_errors=True)

            if update_callback:
                update_callback(100, "Complete")

            logger.info("=== NORTHWEST OUTDOORS PROMO DOWNLOAD COMPLETE ===")

            if not found_promo:
                logger.warning("No promo files found in download")
                return False

            return True

        except Exception as e:
            logger.error(f"Error in Northwest Outdoors promo download: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.should_auto_close_browser():
                self.browser_manager.close_browser()
