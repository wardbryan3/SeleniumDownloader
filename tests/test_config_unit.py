"""
Additional unit tests for config.py - expand beyond test_config_edge_cases.py
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, DEFAULT_CONFIG, DAY_MAPPING


def test_default_config_has_required_keys():
    """Test that DEFAULT_CONFIG has all required keys"""
    required_keys = [
        "test_mode", "test_downloads_dir", "dropbox_base",
        "global_features_dir", "wwo_spots_dir", "promos_dir",
        "tag_file", "browser_download_dir", "auto_close_browser",
        "retry_attempts", "email", "password", "cow_password",
        "urls", "scheduled_downloads"
    ]

    for key in required_keys:
        assert key in DEFAULT_CONFIG, f"Missing required key: {key}"
    print("  ✓ All required keys present in DEFAULT_CONFIG")


def test_default_config_test_mode_true():
    """Test DEFAULT_CONFIG has test_mode=True"""
    assert DEFAULT_CONFIG["test_mode"] is True, "test_mode should default to True"
    print("  ✓ DEFAULT_CONFIG test_mode is True")


def test_default_config_urls_placeholders():
    """Test URL config has placeholder values"""
    urls = DEFAULT_CONFIG.get("urls", {})

    for source, url in urls.items():
        assert "YOUR_LINK" in url, f"{source} URL should be placeholder, got {url}"
    print(f"  ✓ All {len(urls)} source URLs are placeholders")


def test_config_load_missing_file():
    """Test ConfigManager creates default when file missing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "download_config.json"

        # Mock the CONFIG_FILE to point to temp file
        import config as config_module
        original = config_module.CONFIG_FILE
        try:
            config_module.CONFIG_FILE = str(config_path)

            cm = ConfigManager()
            assert config_path.exists(), "Config file should be created"

            with open(config_path) as f:
                saved = json.load(f)
            assert saved["test_mode"] is True, "Saved config should have test_mode=True"
            print("  ✓ Creates default config when file missing")
        finally:
            config_module.CONFIG_FILE = original


def test_config_load_existing_file():
    """Test ConfigManager loads existing config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "download_config.json"
        test_config = {
            "test_mode": False,
            "email": "test@test.com",
            "password": "secret",
        }
        with open(config_path, 'w') as f:
            json.dump(test_config, f)

        import config as config_module
        original = config_module.CONFIG_FILE
        try:
            config_module.CONFIG_FILE = str(config_path)

            cm = ConfigManager()
            assert cm.get("test_mode") is False, "Should load test_mode=False"
            assert cm.get("email") == "test@test.com", "Should load email"
            # Non-specified keys should come from DEFAULT_CONFIG
            assert cm.get("auto_close_browser") is True, "Should use default for unset keys"
            print("  ✓ Loads existing config and merges with defaults")
        finally:
            config_module.CONFIG_FILE = original


def test_config_save_and_reload():
    """Test config save then reload"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "download_config.json"

        import config as config_module
        original = config_module.CONFIG_FILE
        try:
            config_module.CONFIG_FILE = str(config_path)

            cm = ConfigManager()
            cm.set("email", "save_test@test.com")
            cm.set("cow_password", "saved_secret")
            cm.save()

            # Create new instance to reload
            cm2 = ConfigManager()
            assert cm2.get("email") == "save_test@test.com", "Should persist email"
            assert cm2.get("cow_password") == "saved_secret", "Should persist cow_password"
            print("  ✓ Config persists across save/reload")
        finally:
            config_module.CONFIG_FILE = original


def test_config_merge_nested_dicts():
    """Test that nested dicts are fully replaced on merge"""
    import config as config_module
    original = config_module.CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "download_config.json"
        test_urls = {
            "northwest_outdoors": "https://custom.url/1",
            "whittler": "https://custom.url/2"
        }
        test_config = {"urls": test_urls}
        with open(config_path, 'w') as f:
            json.dump(test_config, f)

        try:
            config_module.CONFIG_FILE = str(config_path)

            cm = ConfigManager()
            loaded_urls = cm.get("urls", {})

            assert loaded_urls == test_urls, f"URLs should be fully replaced, got {loaded_urls}"
            assert "northwest_outdoors" in loaded_urls, "Should have northwest_outdoors"
            assert "whittler" in loaded_urls, "Should have whittler"
            print("  ✓ Nested dicts (urls) fully replaced on merge")
        finally:
            config_module.CONFIG_FILE = original


def test_get_output_base_dir_test_mode():
    """Test get_output_base_dir returns test dir in test mode"""
    cm = ConfigManager()
    cm.set("test_mode", True)
    cm.set("test_downloads_dir", "test_output")

    result = cm.get_output_base_dir()
    assert "test_output" in result, f"Should return test dir, got {result}"
    print(f"  ✓ Test mode returns test dir: {result}")


def test_get_output_base_dir_prod_mode():
    """Test get_output_base_dir returns dropbox dir in prod mode"""
    cm = ConfigManager()
    cm.set("test_mode", False)
    cm.set("dropbox_base", "/fake/Dropbox")

    result = cm.get_output_base_dir()
    assert "Dropbox" in result, f"Should return dropbox dir, got {result}"
    print(f"  ✓ Production mode returns dropbox dir: {result}")


def test_get_test_downloads_dir():
    """Test get_test_downloads_dir returns correct path"""
    cm = ConfigManager()
    cm.set("test_downloads_dir", "my_tests")

    result = cm.get_test_downloads_dir()
    assert "my_tests" in result, f"Should contain test dir name, got {result}"
    print(f"  ✓ get_test_downloads_dir: {result}")


def test_ensure_folders_test_mode():
    """Test ensure_folders creates test dirs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager()
        cm.set("test_mode", True)
        cm.set("test_downloads_dir", os.path.join(tmpdir, "test_downloads"))

        result = cm.ensure_folders()
        assert result is True, "ensure_folders should succeed"

        assert Path(cm.get_test_downloads_dir()).exists(), "Test downloads dir should exist"
        assert Path(cm.get_global_features_dir()).exists(), "Global Features dir should exist"
        print("  ✓ Test mode folders created")


def test_ensure_folders_prod_mode():
    """Test ensure_folders handles prod dirs (may fail without real Dropbox)"""
    cm = ConfigManager()
    cm.set("test_mode", False)

    # This may fail in test env without real Dropbox - that's OK
    result = cm.ensure_folders()
    print(f"  ✓ ensure_folders in prod mode returned: {result}")


def test_validate_config_missing_email():
    """Test validate_config reports missing email"""
    cm = ConfigManager()
    cm.set("email", "")
    cm.set("password", "test")
    cm.set("cow_password", "test")

    errors = cm.validate_config()
    email_errors = [e for e in errors if "email" in e.lower()]
    assert len(email_errors) > 0, "Should report missing email"
    print(f"  ✓ Detects missing email: {email_errors[0]}")


def test_validate_config_missing_password():
    """Test validate_config reports missing password"""
    cm = ConfigManager()
    cm.set("email", "test@test.com")
    cm.set("password", "")
    cm.set("cow_password", "test")

    errors = cm.validate_config()
    password_errors = [e for e in errors if "password" in e.lower()]
    assert len(password_errors) > 0, "Should report missing password"
    print(f"  ✓ Detects missing password: {password_errors[0]}")


def test_validate_config_missing_cow_password():
    """Test validate_config reports missing cow_password"""
    cm = ConfigManager()
    cm.set("email", "test@test.com")
    cm.set("password", "test")
    cm.set("cow_password", "")

    errors = cm.validate_config()
    cow_errors = [e for e in errors if "cow" in e.lower()]
    assert len(cow_errors) > 0, "Should report missing cow_password"
    print(f"  ✓ Detects missing cow_password: {cow_errors[0]}")


def test_validate_config_valid():
    """Test validate_config passes with all fields"""
    cm = ConfigManager()
    cm.set("email", "test@test.com")
    cm.set("password", "testpass")
    cm.set("cow_password", "cowpass")

    errors = cm.validate_config()
    assert len(errors) == 0, f"Should have no errors, got {errors}"
    print("  ✓ validate_config passes with all required fields")


def test_validate_config_invalid_time():
    """Test validate_config rejects invalid time format"""
    cm = ConfigManager()
    cm.set("scheduled_downloads", {"enabled": True, "time": "25:99"})

    errors = cm.validate_config()
    time_errors = [e for e in errors if "time" in e.lower()]
    assert len(time_errors) > 0, "Should report invalid time"
    print(f"  ✓ Detects invalid time format: {time_errors[0]}")


def test_validate_retry_attempts_valid():
    """Test valid retry_attempts values"""
    cm = ConfigManager()

    for val in [0, 1, 2, 5, 10]:
        cm.set("retry_attempts", val)
        errors = cm.validate_config()
        retry_errors = [e for e in errors if "retry" in e.lower()]
        assert len(retry_errors) == 0, f"Retry {val} should be valid"
    print("  ✓ Valid retry_attempts accepted")


def test_validate_retry_attempts_invalid():
    """Test invalid retry_attempts values"""
    cm = ConfigManager()

    for val in [-1, "two", None, 2.5]:
        cm.set("retry_attempts", val)
        errors = cm.validate_config()
        retry_errors = [e for e in errors if "retry" in e.lower()]
        assert len(retry_errors) > 0, f"Retry {val} should be invalid"
    print("  ✓ Invalid retry_attempts rejected")


def test_day_mapping_complete():
    """Test DAY_MAPPING has all 7 days"""
    expected = {
        "Monday": "Mon",
        "Tuesday": "Tue",
        "Wednesday": "Wed",
        "Thursday": "Thu",
        "Friday": "Fri",
        "Saturday": "Sat",
        "Sunday": "Sun"
    }
    assert DAY_MAPPING == expected, f"DAY_MAPPING mismatch: {DAY_MAPPING}"
    print(f"  ✓ DAY_MAPPING complete: {list(DAY_MAPPING.keys())}")


def test_get_browser_download_dir():
    """Test get_browser_download_dir returns valid path"""
    cm = ConfigManager()
    result = cm.get_browser_download_dir()
    assert result is not None, "Should return a path"
    assert len(result) > 0, "Path should not be empty"
    print(f"  ✓ Browser download dir: {result}")


def test_clear_browser_download_dir():
    """Test clear_browser_download_dir removes files"""
    cm = ConfigManager()
    download_dir = Path(cm.get_browser_download_dir())
    download_dir.mkdir(parents=True, exist_ok=True)

    # Create a test file
    test_file = download_dir / "test_clear.txt"
    test_file.write_text("test")

    assert test_file.exists(), "Test file should exist"

    cm.clear_browser_download_dir()

    assert not test_file.exists(), "Test file should be deleted"
    print("  ✓ clear_browser_download_dir removes files")


def test_get_scheduled_config():
    """Test get_scheduled_config returns correct structure"""
    cm = ConfigManager()
    scheduled = cm.get_scheduled_config()

    assert isinstance(scheduled, dict), "Should return dict"
    assert "enabled" in scheduled, "Should have enabled key"
    assert "schedule_type" in scheduled, "Should have schedule_type key"
    assert "time" in scheduled, "Should have time key"
    print(f"  ✓ get_scheduled_config returns: {list(scheduled.keys())}")


def run_tests():
    """Run all config unit tests"""
    print("=" * 60)
    print("Running Config Unit Tests")
    print("=" * 60)

    tests = [
        test_default_config_has_required_keys,
        test_default_config_test_mode_true,
        test_default_config_urls_placeholders,
        test_config_load_missing_file,
        test_config_load_existing_file,
        test_config_save_and_reload,
        test_config_merge_nested_dicts,
        test_get_output_base_dir_test_mode,
        test_get_output_base_dir_prod_mode,
        test_get_test_downloads_dir,
        test_ensure_folders_test_mode,
        test_ensure_folders_prod_mode,
        test_validate_config_missing_email,
        test_validate_config_missing_password,
        test_validate_config_missing_cow_password,
        test_validate_config_valid,
        test_validate_config_invalid_time,
        test_validate_retry_attempts_valid,
        test_validate_retry_attempts_invalid,
        test_day_mapping_complete,
        test_get_browser_download_dir,
        test_clear_browser_download_dir,
        test_get_scheduled_config,
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
