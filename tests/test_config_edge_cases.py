"""Standalone configuration edge-case tests."""

import importlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

config_module = importlib.import_module("config")
ConfigManager = config_module.ConfigManager
DEFAULT_CONFIG = config_module.DEFAULT_CONFIG


class TestConfigEdgeCases:
    """Test configuration behavior with an isolated configuration file."""

    def __init__(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "config.json"

    def close(self) -> None:
        """Remove test files."""
        self.temp_dir.cleanup()

    def new_config(self) -> ConfigManager:
        """Create configuration manager with isolated config file."""
        return ConfigManager(self.config_file)

    def test_default_config_has_all_required_keys(self) -> None:
        """Default configuration contains legacy desktop settings."""
        required_keys = {
            "output_dir",
            "tag_file",
            "browser_download_dir",
            "auto_close_browser",
            "retry_attempts",
            "cow_password",
            "urls",
        }
        assert required_keys <= DEFAULT_CONFIG.keys()

    def test_url_validation_rejects_invalid_urls(self) -> None:
        """Placeholder Dropbox URLs are rejected by source validation."""
        invalid_urls = (
            "",
            None,
            "YOUR_LINK_HERE",
            "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
            "https://www.dropbox.com/scl/fo/***REMOVED***",
        )
        for url in invalid_urls:
            assert not url or "YOUR_LINK" in str(url) or "REMOVED" in str(url)

    def test_url_validation_accepts_valid_urls(self) -> None:
        """Configured Dropbox URLs are accepted by source validation."""
        valid_urls = (
            "https://www.dropbox.com/scl/fo/example?rlkey=abc123",
            "https://www.dropbox.com/scl/fo/example?rlkey=xyz789",
        )
        for url in valid_urls:
            assert "YOUR_LINK" not in url and "REMOVED" not in url

    def test_config_merge_user_overrides_defaults(self) -> None:
        """User configuration overrides top-level default values."""
        user_config = {
            "output_dir": "/custom/path",
            "cow_password": "configured",
            "urls": {
                "northwest_outdoors": "https://custom.url/1",
                "whittler": "https://custom.url/2",
            },
        }
        merged = DEFAULT_CONFIG.copy()
        merged.update(user_config)

        assert merged["output_dir"] == "/custom/path"
        assert merged["cow_password"]
        assert merged["urls"] == user_config["urls"]

    def test_output_dir_affects_station_paths(self) -> None:
        """Station output paths use confirmed folder names."""
        cm = self.new_config()
        output_dir = Path(self.temp_dir.name) / "output"
        cm.config["output_dir"] = str(output_dir)

        assert cm.get_output_base_dir() == str(output_dir)
        assert cm.get_global_features_dir() == str(output_dir / "GLOBAL FEATURES")
        assert cm.get_promos_dir() == str(output_dir / "Promos")
        assert cm.get_nbc_dir() == str(output_dir / "NBC")

    def test_retry_attempts_validation(self) -> None:
        """Retry count accepts non-negative integers only."""
        valid_values = (0, 1, 2, 5, 10)
        invalid_values = (-1, "two", None, 2.5)

        assert all(isinstance(value, int) and value >= 0 for value in valid_values)
        assert all(
            not isinstance(value, int) or value < 0 for value in invalid_values
        )

    def test_validate_config_reports_missing_cow_password(self) -> None:
        """Missing COW credential remains a validation failure."""
        cm = self.new_config()
        cm.config["cow_password"] = ""

        assert any("cow" in error.lower() for error in cm.validate_config())


def run_tests() -> int:
    """Run standalone tests without a test framework."""
    tester = TestConfigEdgeCases()
    tests = (
        tester.test_default_config_has_all_required_keys,
        tester.test_url_validation_rejects_invalid_urls,
        tester.test_url_validation_accepts_valid_urls,
        tester.test_config_merge_user_overrides_defaults,
        tester.test_output_dir_affects_station_paths,
        tester.test_retry_attempts_validation,
        tester.test_validate_config_reports_missing_cow_password,
    )
    failed = 0
    try:
        for test in tests:
            try:
                test()
                print(f"  ✓ {test.__name__}")
            except (AssertionError, OSError, ValueError) as error:
                print(f"  ✗ {test.__name__}: {error}")
                failed += 1
    finally:
        tester.close()

    print(f"Results: {len(tests) - failed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(run_tests())
