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

def get_default_browser_download_dir() -> str:
    """Get platform-appropriate browser download directory"""
    project_root = Path(__file__).parent
    if sys.platform == "win32":
        return str(project_root / "browser_downloads")
    else:
        return str(project_root / "browser_downloads")

BROWSER_DOWNLOAD_DIR = get_default_browser_download_dir()

DEFAULT_CONFIG = {
    "output_dir": "downloads",
    "tag_file": "",
    "browser_download_dir": BROWSER_DOWNLOAD_DIR,
    "auto_close_browser": True,
    "retry_attempts": 2,
    "cow_password": "",
    "witc_ftp_server": "",
    "witc_ftp_username": "",
    "witc_ftp_password": "",
    "urls": {
        "northwest_outdoors": "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
        "whittler": "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE"
    }
}

DOWNLOAD_SOURCES = {
    "Melinda Myers": "melinda_myers",
    "Northwest Outdoors": "northwest_outdoors",
    "Whittler": "whittler",
    "Clear Out West": "clear_out_west",
    "Weekend In The Country": "weekend_in_the_country"
}

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config = self.load_config()
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        logger.info(f"Loading config from: {CONFIG_FILE}")
        try:
            if os.path.exists(CONFIG_FILE):
                logger.info("Config file exists, loading...")
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    logger.info(f"Saved config URLs: {saved_config.get('urls', {})}")
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(saved_config)
                    logger.info("Configuration loaded successfully")
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
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_output_base_dir(self) -> str:
        """Get base output directory"""
        output_dir = self.config.get("output_dir", "downloads")
        p = Path(output_dir)
        if not p.is_absolute():
            p = Path.cwd() / p
        return str(p)
    
    def _get_subdir(self, relative_path: str) -> str:
        """Get a subdirectory under the output directory"""
        return os.path.join(self.get_output_base_dir(), relative_path)
    
    def ensure_folders(self) -> bool:
        """Ensure all required output folders exist"""
        folders = [
            self.get_output_base_dir(),
            self.get_global_features_dir(),
            self.get_promos_dir(),
            self.get_spots_dir(),
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
        
        if not config.get("cow_password"):
            errors.append("COW password is required")
        
        folders_to_check = [
            ("Base output", self.get_output_base_dir()),
            ("GLOBAL FEATURES", self.get_global_features_dir()),
            ("Promos", self.get_promos_dir()),
            ("Spots", self.get_spots_dir()),
        ]
        
        for name, folder in folders_to_check:
            if folder:
                try:
                    Path(folder).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create {name} folder: {e}")
        
        retry_attempts = config.get("retry_attempts", 2)
        if not isinstance(retry_attempts, int) or retry_attempts < 0:
            errors.append("Retry attempts must be a positive integer")
        
        return errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a single configuration value"""
        self.config[key] = value
    
    def save(self) -> bool:
        """Save configuration to file (alias for save_config)"""
        return self.save_config()
    
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        self.config.update(updates)
        self.save_config()
    
    def get_global_features_dir(self) -> str:
        """Get the Global Features directory under the output dir"""
        return self._get_subdir("GLOBAL FEATURES")
    
    def get_promos_dir(self) -> str:
        """Get the Promos directory under the output dir"""
        return self._get_subdir("Promos")
    
    def get_spots_dir(self) -> str:
        """Get the Spots directory under the output dir"""
        return self._get_subdir("Spots")
    
    def get_tag_file(self) -> str:
        """Get the audio tag file path"""
        config_tag_file = self.config.get("tag_file")
        if config_tag_file:
            return config_tag_file
        return os.path.join(self.get_promos_dir(), "NWKORVTAG.wav")
    
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
