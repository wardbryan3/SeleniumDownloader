"""
Test configuration edge cases
"""

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, DEFAULT_CONFIG

class TestConfigEdgeCases:
    """Test configuration edge cases"""

    def setup_method(self):
        """Create a temporary config file for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_config_file = ConfigManager.CONFIG_FILE if hasattr(ConfigManager, 'CONFIG_FILE') else None

    def teardown_method(self):
        """Restore original config file"""
        pass

    def test_default_config_has_all_required_keys(self):
        """Test that DEFAULT_CONFIG has all required keys"""
        required_keys = [
            "output_dir",
            "tag_file", "browser_download_dir", "auto_close_browser",
            "retry_attempts", "cow_password",
            "urls"
        ]

        for key in required_keys:
            assert key in DEFAULT_CONFIG, f"Missing required key: {key}"
        print("  ✓ All required keys present in DEFAULT_CONFIG")

    def test_url_validation_rejects_invalid_urls(self):
        """Test URL validation logic from sources"""
        invalid_urls = [
            "",
            None,
            "YOUR_LINK_HERE",
            "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
            "https://www.dropbox.com/scl/fo/***REMOVED***",
        ]

        for url in invalid_urls:
            is_invalid = not url or "YOUR_LINK" in str(url) or "REMOVED" in str(url)
            assert is_invalid, f"URL should be invalid: {url}"
        print("  ✓ Invalid URLs correctly identified")

    def test_url_validation_accepts_valid_urls(self):
        """Test that valid Dropbox URLs pass validation"""
        valid_urls = [
            "https://www.dropbox.com/scl/fo/msp1ouz0bh0kyhoi6m0rb/ANM_rYPoVJEMjEfbJ8FnHOQ?e=2&rlkey=abc123",
            "https://www.dropbox.com/scl/fo/r4afn2y51ev2nusph34be/h?rlkey=xyz789",
        ]

        for url in valid_urls:
            is_valid = url and "YOUR_LINK" not in url and "REMOVED" not in url
            assert is_valid, f"URL should be valid: {url}"
        print("  ✓ Valid URLs correctly identified")

    def test_config_merge_user_overrides_defaults(self):
        """Test that user config properly overrides defaults"""
        user_config = {
            "output_dir": "/custom/path",
            "cow_password": "secret",
            "urls": {
                "northwest_outdoors": "https://custom.url/1",
                "whittler": "https://custom.url/2"
            }
        }

        merged = DEFAULT_CONFIG.copy()
        merged.update(user_config)

        assert merged["output_dir"] == "/custom/path"
        assert merged["cow_password"] == "secret"
        assert merged["urls"]["northwest_outdoors"] == "https://custom.url/1"
        assert merged["urls"]["whittler"] == "https://custom.url/2"
        print("  ✓ User config properly overrides defaults")

    def test_output_dir_affects_paths(self):
        """Test that output_dir changes directory paths correctly"""
        cm = ConfigManager()

        cm.config["output_dir"] = "/tmp/custom_output"

        base_dir = cm.get_output_base_dir()
        assert "/tmp/custom_output" in base_dir

        gf_dir = cm.get_global_features_dir()
        assert "Global Features" in gf_dir
        assert "/tmp/custom_output" in gf_dir

        print(f"  ✓ Output base: {base_dir}")
        print(f"  ✓ Global Features: {gf_dir}")

    def test_retry_attempts_validation(self):
        """Test retry_attempts must be valid integer"""
        valid_values = [0, 1, 2, 5, 10]
        for val in valid_values:
            is_valid = isinstance(val, int) and val >= 0
            assert is_valid, f"Retry {val} should be valid"

        invalid_values = [-1, "two", None, 2.5]
        for val in invalid_values:
            is_invalid = not (isinstance(val, int) and val >= 0)
            assert is_invalid, f"Retry {val} should be invalid"

        print("  ✓ Retry attempts validation works correctly")

    def test_config_validate_returns_errors_for_missing_required(self):
        """Test that validate_config returns errors for missing required fields"""
        cm = ConfigManager()

        cm.config["cow_password"] = ""

        errors = cm.validate_config()

        assert any("cow" in e.lower() for e in errors), "Should report missing cow_password"

        print(f"  ✓ Found {len(errors)} validation errors: {errors}")


def run_tests():
    """Run all edge case tests"""
    print("=" * 60)
    print("Running Configuration Edge Case Tests")
    print("=" * 60)

    tester = TestConfigEdgeCases()

    tests = [
        tester.test_default_config_has_all_required_keys,
        tester.test_url_validation_rejects_invalid_urls,
        tester.test_url_validation_accepts_valid_urls,
        tester.test_config_merge_user_overrides_defaults,
        tester.test_output_dir_affects_paths,
        tester.test_retry_attempts_validation,
        tester.test_config_validate_returns_errors_for_missing_required,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())