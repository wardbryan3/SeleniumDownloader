"""
Configuration management for Audio Download Manager
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Detect if running as frozen executable (PyInstaller) or Python script
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    APP_DIR = Path(sys.executable).parent
else:
    # Running as Python script
    APP_DIR = Path(__file__).parent

CONFIG_FILE = str(APP_DIR / "download_config.json")

def get_default_dropbox_path() -> str:
    """Get platform-appropriate default Dropbox path"""
    if sys.platform == "win32":
        return r"D:\users\935ko\Dropbox"
    else:
        return str(Path.home() / "Dropbox")

def get_default_browser_download_dir() -> str:
    """Get platform-appropriate browser download directory"""
    project_root = Path(__file__).parent
    if sys.platform == "win32":
        return str(project_root / "browser_downloads")
    else:
        return str(project_root / "browser_downloads")

DROPBOX_BASE = get_default_dropbox_path()
GLOBAL_FEATURES_PATH = os.path.join(DROPBOX_BASE, "Global Features")
WWO_SPOTS_PATH = os.path.join(DROPBOX_BASE, "WWO SPOTS")
PROMOS_PATH = os.path.join(DROPBOX_BASE, "Promos")
TAG_FILE_PATH = os.path.join(PROMOS_PATH, "NWKORVTAG.wav")
BROWSER_DOWNLOAD_DIR = get_default_browser_download_dir()

TEST_MODE_DEFAULT = True

DEFAULT_CONFIG = {
    "test_mode": TEST_MODE_DEFAULT,
    "test_downloads_dir": "downloads",
    "dropbox_base": DROPBOX_BASE,
    "global_features_dir": GLOBAL_FEATURES_PATH,
    "wwo_spots_dir": WWO_SPOTS_PATH,
    "promos_dir": PROMOS_PATH,
    "tag_file": TAG_FILE_PATH,
    "browser_download_dir": BROWSER_DOWNLOAD_DIR,
    "auto_close_browser": True,
    "retry_attempts": 2,
    "email": "",
    "password": "",
    "cow_password": "***REMOVED***",
    "scheduled_downloads": {
        "enabled": False,
        "schedule_type": "daily",
        "time": "06:00",
        "days": [],
        "download_all": True,
        "selected_sources": []
    }
}

DAY_MAPPING = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
    "Sunday": "Sun"
}

DOWNLOAD_SOURCES = {
    "Melinda Myers": "melinda_myers",
    "Northwest Outdoors": "northwest_outdoors",
    "Whittler": "whittler",
    "Westwood One": "westwood_one",
    "Clear Out West": "clear_out_west"
}

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config = self.load_config()
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(saved_config)
                    logger.info("Configuration loaded successfully")
                    
                    test_mode = merged_config.get("test_mode", TEST_MODE_DEFAULT)
                    logger.info(f"Test mode: {test_mode}")
                    
                    return merged_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        logger.info("Using default configuration")
        default_config = DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info("Created default configuration file")
        except Exception as e:
            logger.error(f"Could not create config file: {e}")
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        if config is not None:
            self.config = config
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.config.get("test_mode", TEST_MODE_DEFAULT)
    
    def get_test_downloads_dir(self) -> str:
        """Get the local test downloads directory"""
        base = Path.cwd() / self.config.get("test_downloads_dir", "downloads")
        return str(base)
    
    def get_output_base_dir(self) -> str:
        """Get base output directory (test or production)"""
        if self.is_test_mode():
            return self.get_test_downloads_dir()
        else:
            return self.config.get("dropbox_base", DROPBOX_BASE)
    
    def _get_dir_for_mode(self, relative_path: str) -> str:
        """Get a directory path, adjusted for test mode"""
        if self.is_test_mode():
            return os.path.join(self.get_test_downloads_dir(), relative_path)
        else:
            return os.path.join(self.config.get("dropbox_base", DROPBOX_BASE), relative_path)
    
    def ensure_folders(self) -> bool:
        """Ensure all required output folders exist"""
        if self.is_test_mode():
            folders = [
                self.get_test_downloads_dir(),
                self.get_global_features_dir(),
                self.get_wwo_spots_dir(),
                self.get_promos_dir(),
            ]
        else:
            folders = [
                self.config.get("dropbox_base"),
                self.config.get("global_features_dir"),
                self.config.get("wwo_spots_dir"),
                self.config.get("promos_dir"),
            ]
        
        for folder in folders:
            if folder:
                try:
                    Path(folder).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Could not create folder {folder}: {e}")
                    return False
        return True
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        config = self.config
        
        if not config.get("email"):
            errors.append("Email is required for Westwood One downloads")
        if not config.get("password"):
            errors.append("Password is required for Westwood One downloads")
        
        if not config.get("cow_password"):
            errors.append("COW password is required")
        
        tag_file = config.get("tag_file")
        if tag_file and not Path(tag_file).exists():
            if not self.is_test_mode():
                errors.append(f"Tag file not found: {tag_file}")
        
        folders_to_check = [
            ("test" if self.is_test_mode() else "production", self.get_output_base_dir()),
        ]
        
        if self.is_test_mode():
            folders_to_check.extend([
                ("Global Features", self.get_global_features_dir()),
                ("WWO SPOTS", self.get_wwo_spots_dir()),
                ("Promos", self.get_promos_dir()),
            ])
        
        for name, folder in folders_to_check:
            if folder:
                try:
                    Path(folder).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create {name} folder: {e}")
        
        retry_attempts = config.get("retry_attempts", 2)
        if not isinstance(retry_attempts, int) or retry_attempts < 0:
            errors.append("Retry attempts must be a positive integer")
        
        scheduled = config.get("scheduled_downloads", {})
        if scheduled.get("enabled", False):
            time_str = scheduled.get("time", "")
            try:
                from datetime import datetime
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                errors.append(f"Invalid time format: {time_str}")
        
        return errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        self.config.update(updates)
        self.save_config()
    
    def get_scheduled_config(self) -> Dict[str, Any]:
        """Get scheduled downloads configuration"""
        return self.config.get("scheduled_downloads", {})
    
    def get_global_features_dir(self) -> str:
        """Get the Global Features directory (test or production)"""
        return self._get_dir_for_mode("Global Features")
    
    def get_wwo_spots_dir(self) -> str:
        """Get the WWO SPOTS directory (test or production)"""
        return self._get_dir_for_mode("WWO SPOTS")
    
    def get_promos_dir(self) -> str:
        """Get the Promos directory (test or production)"""
        return self._get_dir_for_mode("Promos")
    
    def get_tag_file(self) -> str:
        """Get the audio tag file path (test or production)"""
        if self.is_test_mode():
            tag_name = Path(TAG_FILE_PATH).name
            return os.path.join(self.get_promos_dir(), tag_name)
        return self.config.get("tag_file", TAG_FILE_PATH)
    
    def get_browser_download_dir(self) -> str:
        """Get the dedicated browser download directory"""
        return self.config.get("browser_download_dir", BROWSER_DOWNLOAD_DIR)
    
    def clear_browser_download_dir(self):
        """Clear the browser download directory before starting downloads"""
        download_dir = Path(self.get_browser_download_dir())
        download_dir.mkdir(parents=True, exist_ok=True)
        
        for f in download_dir.iterdir():
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    import shutil
                    shutil.rmtree(f)
            except Exception as e:
                logger.warning(f"Could not delete {f}: {e}")
    
    def get_browser_download_files(self) -> set:
        """Get the set of files currently in browser download directory"""
        download_dir = Path(self.get_browser_download_dir())
        files = set()
        if download_dir.exists():
            for f in download_dir.iterdir():
                if f.is_file():
                    files.add(f.name)
        return files
