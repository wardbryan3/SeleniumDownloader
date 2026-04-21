"""
Browser management for Selenium operations
"""

import logging
from typing import Optional, List, Dict
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager

from constants import ALLOWED_EXTENSIONS, EXCLUDED_EXTENSIONS, EXCLUDED_PREFIXES

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser lifecycle and operations"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.driver: Optional[webdriver.Firefox] = None
        self._initialize_download_directory()
    
    def _get_temp_download_dir(self) -> str:
        """Get the dedicated download directory for the browser"""
        download_dir = self.config_manager.get_browser_download_dir()
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        return download_dir
    
    def _initialize_download_directory(self):
        """Ensure download directory exists"""
        download_dir = self._get_temp_download_dir()
        Path(download_dir).mkdir(parents=True, exist_ok=True)
    
    def _create_browser_options(self) -> Options:
        """Create and configure browser options"""
        options = Options()
        download_dir = self._get_temp_download_dir()
        
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", str(Path(download_dir).resolve()))
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                             "application/zip, audio/mpeg, application/octet-stream")
        options.set_preference("media.play-stand-alone", False)
        options.set_preference("pdfjs.disabled", True)
        
        options.set_preference("browser.download.manager.useWindow", False)
        options.set_preference("browser.download.manager.focusWhenStarting", False)
        options.set_preference("browser.download.manager.showAlertOnComplete", False)
        options.set_preference("browser.download.manager.closeWhenDone", False)
        
        return options
    
    def start_browser(self) -> bool:
        """Start the browser if not already running"""
        if self.driver is not None:
            logger.info("Browser already running")
            return True
        
        try:
            options = self._create_browser_options()
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Maximize window to avoid element obscuring
            self.driver.maximize_window()
            
            logger.info("Browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            return False
    
    def close_browser(self):
        """Close the browser if it's open"""
        if self.driver is not None:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
    
    def get_driver(self) -> Optional[webdriver.Firefox]:
        """Get the browser driver, starting it if necessary"""
        if self.driver is None:
            if not self.start_browser():
                return None
        return self.driver
    
    def is_browser_open(self) -> bool:
        """Check if browser is currently open"""
        return self.driver is not None
    
    def get_browser_downloads(self, timeout: int = 5) -> List[Dict]:
        """
        Get the list of downloads from Firefox's about:downloads page.
        Returns list of dicts with: name, path, state, size
        """
        if not self.driver:
            logger.debug("No driver, returning empty downloads")
            return []
        
        try:
            self.driver.get("about:downloads")
            
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located(("css selector", "#downloadsList")))
            
            download_items = self.driver.execute_script("""
                const list = document.getElementById('downloadsList');
                if (!list) return [];
                
                const items = list.querySelectorAll('richlistitem');
                const downloads = [];
                
                items.forEach(item => {
                    const nameEl = item.querySelector('.downloadTarget');
                    const stateEl = item.querySelector('.downloadState');
                    const progressEl = item.querySelector('.downloadProgress');
                    const fileSizeEl = item.querySelector('.downloadSize');
                    
                    if (nameEl) {
                        downloads.push({
                            name: nameEl.textContent.trim(),
                            state: stateEl ? stateEl.textContent.trim() : 'unknown',
                            progress: progressEl ? progressEl.value : 100,
                            size: fileSizeEl ? fileSizeEl.textContent.trim() : 'unknown'
                        });
                    }
                });
                
                return downloads;
            """)
            
            if download_items:
                logger.info(f"Browser downloads found: {len(download_items)} items")
                for item in download_items:
                    logger.info(f"  - {item.get('name', '?')}: state={item.get('state', '?')}, progress={item.get('progress', '?')}%")
            else:
                logger.debug("No downloads in browser")
            
            return download_items
            
        except TimeoutException:
            logger.debug("Timeout waiting for about:downloads page")
            return []
        except Exception as e:
            logger.debug(f"Error getting browser downloads: {e}")
            return []
    
    def wait_for_browser_download_complete(self, timeout: int = 60, poll_interval: float = 1.0) -> str:
        """
        Wait for Firefox to report a download as complete.
        Returns the file path of the completed download, or None if timeout.
        Only accepts audio/document archive files.
        """
        import time
        download_dir = Path(self._get_temp_download_dir())
        
        start_time = time.time()
        checked_files = set()
        
        while time.time() - start_time < timeout:
            downloads = self.get_browser_downloads(timeout=3)
            
            for dl in downloads:
                name = dl.get('name', '')
                state = dl.get('state', '').lower()
                progress = dl.get('progress', 0)
                
                if not name:
                    continue
                
                file_path = download_dir / name
                
                if file_path.exists():
                    try:
                        size = file_path.stat().st_size
                        if size > 0:
                            if progress >= 100 or 'complete' in state or 'finished' in state or state == '':
                                if name not in checked_files:
                                    checked_files.add(name)
                                    logger.info(f"Browser confirmed download complete: {name} ({size} bytes)")
                                    return str(file_path)
                            else:
                                logger.debug(f"Download in progress: {name} ({progress}%, {size} bytes)")
                    except OSError:
                        continue
            
            time.sleep(poll_interval)
        
        for f in download_dir.iterdir():
            if f.is_file():
                try:
                    size = f.stat().st_size
                    if size > 0 and f.name not in checked_files:
                        has_excluded_ext = any(f.name.endswith(ext) for ext in EXCLUDED_EXTENSIONS)
                        has_excluded_prefix = any(f.name.startswith(prefix) for prefix in EXCLUDED_PREFIXES)
                        has_allowed_ext = any(f.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)
                        
                        if has_excluded_ext or has_excluded_prefix:
                            logger.debug(f"Ignoring system/temp file: {f.name}")
                        elif has_allowed_ext:
                            checked_files.add(f.name)
                            logger.info(f"Found valid download: {f.name} ({size} bytes)")
                            return str(f)
                        else:
                            logger.debug(f"Ignoring unknown file type: {f.name}")
                except OSError:
                    continue
        
        logger.warning(f"Browser download wait timeout after {timeout}s")
        return None