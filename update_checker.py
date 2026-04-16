"""
GitHub update checker for Audio Download Manager
"""

import logging
import urllib.request
import json
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

GITHUB_REPO = "wardbryan3/SeleniumDownloader"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateChecker:
    """Check for application updates via GitHub Releases API"""
    
    def __init__(self, current_version: str):
        self.current_version = current_version
        self._latest_version: Optional[str] = None
        self._download_url: Optional[str] = None
        self._release_notes: Optional[str] = None
    
    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, ...]:
        """Parse version string into tuple of integers for comparison"""
        match = re.search(r'(\d+)\.(\d+)\.?(\d*)', version_str)
        if match:
            parts = [int(match.group(1)), int(match.group(2))]
            if match.group(3):
                parts.append(int(match.group(3)))
            return tuple(parts)
        return (0, 0, 0)
    
    def check_for_update(self) -> Tuple[bool, str, str, str]:
        """
        Check GitHub for a newer version.
        
        Returns:
            Tuple of (update_available, version, download_url, release_notes)
        """
        try:
            logger.info("Checking for updates...")
            
            req = urllib.request.Request(
                RELEASES_URL,
                headers={
                    'User-Agent': 'SeleniumDownloader/1.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            self._latest_version = data.get('tag_name', '').lstrip('v')
            self._download_url = data.get('html_url', f"https://github.com/{GITHUB_REPO}/releases")
            
            body = data.get('body', '')
            self._release_notes = body[:500] if body else ''
            
            current = self.parse_version(self.current_version)
            latest = self.parse_version(self._latest_version)
            
            if latest > current:
                logger.info(f"Update available: {self._latest_version} (current: {self.current_version})")
                return True, self._latest_version, self._download_url, self._release_notes
            else:
                logger.info(f"No updates available. Current: {self.current_version}, Latest: {self._latest_version}")
                return False, self._latest_version, self._download_url, self._release_notes
                
        except urllib.error.URLError as e:
            logger.debug(f"Could not check for updates (network error): {e}")
            return False, "", "", ""
        except json.JSONDecodeError as e:
            logger.debug(f"Could not parse update response: {e}")
            return False, "", "", ""
        except Exception as e:
            logger.debug(f"Error checking for updates: {e}")
            return False, "", "", ""
    
    @property
    def latest_version(self) -> str:
        return self._latest_version or "unknown"
    
    @property
    def download_url(self) -> str:
        return self._download_url or f"https://github.com/{GITHUB_REPO}/releases"


def check_for_updates_async(current_version: str, callback):
    """
    Check for updates in a background thread.
    
    Args:
        current_version: Current application version string
        callback: Function to call with result (update_available, version, url)
    """
    import threading
    
    def _check():
        checker = UpdateChecker(current_version)
        result = checker.check_for_update()
        callback(result)
    
    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
