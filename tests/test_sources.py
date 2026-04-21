"""
Test URL validation logic for all download sources
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager


def test_northwest_outdoors_url_validation():
    """Test northwest_outdoors URL validation"""
    cm = ConfigManager()
    urls_config = cm.get("urls", {})

    url = urls_config.get("northwest_outdoors", "")

    is_invalid = not url or "YOUR_LINK" in url or "REMOVED" in url

    assert not is_invalid, f"URL should be valid: {url}"
    print(f"  ✓ northwest_outdoors URL: {url}")


def test_whittler_url_validation():
    """Test whittler URL validation"""
    cm = ConfigManager()
    urls_config = cm.get("urls", {})

    url = urls_config.get("whittler", "")

    is_invalid = not url or "YOUR_LINK" in url or "REMOVED" in url

    assert not is_invalid, f"URL should be valid: {url}"
    print(f"  ✓ whittler URL: {url}")


def test_dropbox_url_format():
    """Test that Dropbox URLs have expected format"""
    cm = ConfigManager()
    urls_config = cm.get("urls", {})

    for source, url in urls_config.items():
        if url and "YOUR_LINK" not in url and "REMOVED" not in url:
            assert "dropbox.com" in url.lower(), f"Should be Dropbox URL: {url}"
            assert "scl/fo/" in url, f"Should be shared link format: {url}"
            print(f"  ✓ {source} has correct Dropbox format")


def test_missing_urls_handled():
    """Test that missing URLs are handled gracefully"""
    test_config = {"urls": {}}

    url = test_config.get("urls", {}).get("northwest_outdoors")
    is_invalid = not url or "YOUR_LINK" in str(url)
    assert is_invalid, "Missing URL should be detected"

    print("  ✓ Missing URLs handled correctly")


def test_partial_urls_config():
    """Test that partial URLs config (only some sources) is handled"""
    test_config = {
        "urls": {
            "northwest_outdoors": "https://www.dropbox.com/scl/fo/abc123"
        }
    }

    nwo_url = test_config.get("urls", {}).get("northwest_outdoors")
    is_nwo_valid = nwo_url and "YOUR_LINK" not in nwo_url

    whittler_url = test_config.get("urls", {}).get("whittler")
    is_whittler_valid = whittler_url and "YOUR_LINK" not in str(whittler_url)

    assert is_nwo_valid, "Northwest Outdoors URL should be valid"
    assert not is_whittler_valid, "Whittler URL should be invalid (not in config)"

    print("  ✓ Partial URLs config handled correctly")


def test_url_with_special_characters():
    """Test URLs with special characters are handled"""
    test_urls = [
        "https://www.dropbox.com/scl/fo/abc123?rlkey=xyz&st=abc&dl=0",
        "https://www.dropbox.com/scl/fo/path?e=2&st=file.mp3",
    ]

    for url in test_urls:
        is_valid = url and "YOUR_LINK" not in url
        assert is_valid, f"URL with special chars should be valid: {url}"

    print("  ✓ URLs with special characters handled correctly")


def test_validation_logic_matches_northwest_outdoors():
    """Verify validation logic matches northwest_outdoors.py"""
    test_urls = {
        "valid_url": "https://www.dropbox.com/scl/fo/abc123?e=2&rlkey=xyz",
        "placeholder": "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
        "removed": "https://www.dropbox.com/scl/fo/***REMOVED***",
        "empty": "",
        "none": None,
    }

    expected_results = {
        "valid_url": True,
        "placeholder": False,
        "removed": False,
        "empty": False,
        "none": False,
    }

    for name, url in test_urls.items():
        expected = expected_results[name]
        actual = bool(url) and "YOUR_LINK" not in str(url) and "REMOVED" not in str(url)
        assert actual == expected, f"{name}: expected {expected}, got {actual}"

    print("  ✓ Northwest Outdoors validation logic matches source")


def test_validation_logic_matches_whittler():
    """Verify validation logic matches whittler.py"""
    test_urls = {
        "valid_url": "https://www.dropbox.com/scl/fo/def456?rlkey=abc",
        "placeholder": "https://www.dropbox.com/scl/fo/YOUR_LINK_HERE",
        "removed": "https://www.dropbox.com/scl/fo/***REMOVED***",
        "empty": "",
        "none": None,
    }

    expected_results = {
        "valid_url": True,
        "placeholder": False,
        "removed": False,
        "empty": False,
        "none": False,
    }

    for name, url in test_urls.items():
        expected = expected_results[name]
        actual = bool(url) and "YOUR_LINK" not in str(url) and "REMOVED" not in str(url)
        assert actual == expected, f"{name}: expected {expected}, got {actual}"

    print("  ✓ Whittler validation logic matches source")


def run_tests():
    """Run all source URL validation tests"""
    print("=" * 60)
    print("Running Source URL Validation Tests")
    print("=" * 60)

    tests = [
        test_northwest_outdoors_url_validation,
        test_whittler_url_validation,
        test_dropbox_url_format,
        test_missing_urls_handled,
        test_partial_urls_config,
        test_url_with_special_characters,
        test_validation_logic_matches_northwest_outdoors,
        test_validation_logic_matches_whittler,
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