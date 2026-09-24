"""Configuration management for Audio Download Manager."""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

CONFIG_FILE = str(APP_DIR / "download_config.json")


def get_default_browser_download_dir() -> str:
    """Return browser staging directory."""
    return str(Path(__file__).parent / "browser_downloads")


BROWSER_DOWNLOAD_DIR = get_default_browser_download_dir()

DEFAULT_CONFIG: dict[str, Any] = {
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
        "whittler": "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
    },
}

DOWNLOAD_SOURCES = {
    "Melinda Myers": "melinda_myers",
    "Northwest Outdoors": "northwest_outdoors",
    "Whittler": "whittler",
    "Clear Out West": "clear_out_west",
    "Weekend In The Country": "weekend_in_the_country",
}


class ConfigManager:
    """Manage legacy desktop application configuration."""

    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config_path = Path(config_file or CONFIG_FILE)
        self.config = self.load_config(self.config_path)

    @staticmethod
    def load_config(config_file: str | Path = CONFIG_FILE) -> dict[str, Any]:
        """Load configuration or create a default configuration file."""
        config_path = Path(config_file)
        logger.info("Loading config from: %s", config_path)
        try:
            if config_path.exists():
                with config_path.open(encoding="utf-8") as file_handle:
                    saved_config = json.load(file_handle)
                if not isinstance(saved_config, dict):
                    raise ValueError("configuration root must be an object")
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(saved_config)
                logger.info("Configuration loaded successfully")
                return merged_config
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logger.error("Error loading config: %s", error)

        logger.info("Using default configuration")
        default_config = DEFAULT_CONFIG.copy()
        try:
            with config_path.open("w", encoding="utf-8") as file_handle:
                json.dump(default_config, file_handle, indent=2)
            logger.info("Created default configuration file")
        except OSError as error:
            logger.error("Could not create config file: %s", error)
        return default_config

    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            with self.config_path.open("w", encoding="utf-8") as file_handle:
                json.dump(self.config, file_handle, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except OSError as error:
            logger.error("Error saving config: %s", error)
            return False

    def get_output_base_dir(self) -> str:
        """Return configured output base directory."""
        output_dir = Path(self.config.get("output_dir", "downloads"))
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        return str(output_dir)

    def _get_subdir(self, relative_path: str) -> str:
        """Return one station directory under output directory."""
        return os.path.join(self.get_output_base_dir(), relative_path)

    def ensure_folders(self) -> bool:
        """Create required station output directories."""
        for folder in (
            self.get_output_base_dir(),
            self.get_global_features_dir(),
            self.get_promos_dir(),
            self.get_nbc_dir(),
        ):
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except OSError as error:
                logger.error("Could not create folder %s: %s", folder, error)
                return False
        return True

    def validate_config(self) -> list[str]:
        """Validate configuration and return errors."""
        errors: list[str] = []
        if not self.config.get("cow_password"):
            errors.append("COW password is required")

        for name, folder in (
            ("Base output", self.get_output_base_dir()),
            ("GLOBAL FEATURES", self.get_global_features_dir()),
            ("Promos", self.get_promos_dir()),
            ("NBC", self.get_nbc_dir()),
        ):
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except OSError as error:
                errors.append(f"Cannot create {name} folder: {error}")

        retry_attempts = self.config.get("retry_attempts", 2)
        if not isinstance(retry_attempts, int) or retry_attempts < 0:
            errors.append("Retry attempts must be a non-negative integer")
        return errors

    def get(self, key: str, default: Any = None) -> Any:
        """Return one configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set one configuration value."""
        self.config[key] = value

    def save(self) -> bool:
        """Save configuration."""
        return self.save_config()

    def update(self, updates: dict[str, Any]) -> None:
        """Update and save configuration."""
        self.config.update(updates)
        self.save_config()

    def get_global_features_dir(self) -> str:
        """Return station GLOBAL FEATURES directory."""
        return self._get_subdir("GLOBAL FEATURES")

    def get_promos_dir(self) -> str:
        """Return station Promos directory."""
        return self._get_subdir("Promos")

    def get_nbc_dir(self) -> str:
        """Return station NBC directory."""
        return self._get_subdir("NBC")

    def get_tag_file(self) -> str:
        """Return audio tag file path."""
        return self.config.get("tag_file") or os.path.join(
            self.get_promos_dir(), "NWKORVTAG.wav"
        )

    def get_browser_download_dir(self) -> str:
        """Return dedicated browser staging directory."""
        return self.config.get("browser_download_dir", BROWSER_DOWNLOAD_DIR)

    def clear_browser_download_dir(self) -> None:
        """Clear browser staging directory before a download run."""
        download_dir = Path(self.get_browser_download_dir())
        download_dir.mkdir(parents=True, exist_ok=True)
        for path in download_dir.iterdir():
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            except OSError as error:
                logger.warning("Could not delete %s: %s", path, error)

    def get_browser_download_files(self) -> set[str]:
        """Return names of files in browser staging directory."""
        download_dir = Path(self.get_browser_download_dir())
        if not download_dir.exists():
            return set()
        return {path.name for path in download_dir.iterdir() if path.is_file()}
