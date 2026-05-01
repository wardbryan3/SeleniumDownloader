"""
Tests for update_checker.py - mock HTTP calls to GitHub API
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from update_checker import UpdateChecker


def test_parse_version_valid():
    """Test parse_version with valid version strings"""
    checker = UpdateChecker("1.0.0")

    result = checker.parse_version("1.1.8")
    assert result == (1, 1, 8), f"Expected (1, 1, 8), got {result}"
    print(f"  ✓ parse_version('1.1.8') = {result}")

    result = checker.parse_version("2.0")
    assert result == (2, 0), f"Expected (2, 0), got {result}"
    print(f"  ✓ parse_version('2.0') = {result}")

    result = checker.parse_version("10.20.30")
    assert result == (10, 20, 30), f"Expected (10, 20, 30), got {result}"
    print(f"  ✓ parse_version('10.20.30') = {result}")


def test_parse_version_invalid():
    """Test parse_version with invalid version strings"""
    checker = UpdateChecker("1.0.0")

    # These produce (0,0,0) because regex finds no match
    invalid_versions = ["", "abc", "not-a-version"]
    for v in invalid_versions:
        result = checker.parse_version(v)
        assert result == (0, 0, 0), f"Expected (0, 0, 0) for '{v}', got {result}"

    # "v1.0" matches regex and returns (1, 0) - this is acceptable behavior
    result = checker.parse_version("v1.0")
    assert result == (1, 0) or result == (1, 0, 0), f"Expected (1, 0) for 'v1.0', got {result}"

    # "1.0.0.0" - regex only captures first 3 parts
    result = checker.parse_version("1.0.0.0")
    assert result == (1, 0, 0), f"Expected (1, 0, 0) for '1.0.0.0', got {result}"

    print("  ✓ parse_version handles invalid versions correctly")


def test_parse_version_none():
    """Test parse_version with None input"""
    checker = UpdateChecker("1.0.0")
    try:
        result = checker.parse_version(None)
        # If it doesn't raise, check result
        assert result == (0, 0, 0), f"Expected (0, 0, 0) for None, got {result}"
    except (AttributeError, TypeError):
        # This is acceptable - function may not handle None gracefully
        pass
    print("  ✓ parse_version handles None (may raise or return (0,0,0))")


def test_check_for_update_newer_available():
    """Test check_for_update detects newer version"""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        'tag_name': '2.0.0',
        'html_url': 'https://github.com/wardbryan3/SeleniumDownloader/releases/tag/2.0.0',
        'body': 'Major update with new features'
    }).encode('utf-8')

    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = lambda s, *a: False

    with patch('update_checker.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value = mock_response

        checker = UpdateChecker("1.1.8")
        update_available, version, url, notes = checker.check_for_update()

        assert update_available is True, f"Expected update available, got {update_available}"
        assert version == "2.0.0", f"Expected '2.0.0', got '{version}'"
        assert "github.com" in url, f"Expected github URL, got '{url}'"
        print(f"  ✓ Detected newer version: {version}")


def test_check_for_update_current_is_latest():
    """Test check_for_update when current is latest"""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        'tag_name': '1.1.8',
        'html_url': 'https://github.com/wardbryan3/SeleniumDownloader/releases/tag/1.1.8',
        'body': ''
    }).encode('utf-8')

    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = lambda s, *a: False

    with patch('update_checker.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value = mock_response

        checker = UpdateChecker("1.1.8")
        update_available, version, url, notes = checker.check_for_update()

        assert update_available is False, "Should report no update available"
        assert version == "1.1.8", f"Expected '1.1.8', got '{version}'"
        print(f"  ✓ Correctly reports no update (current is latest)")


def test_check_for_update_network_error():
    """Test check_for_update handles network errors"""
    with patch('update_checker.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network error")

        checker = UpdateChecker("1.1.8")
        update_available, version, url, notes = checker.check_for_update()

        assert update_available is False, "Should return False on error"
        assert version == "", f"Expected empty version, got '{version}'"
        print("  ✓ Handles network errors gracefully")


def test_check_for_update_invalid_json():
    """Test check_for_update handles invalid JSON response"""
    mock_response = MagicMock()
    mock_response.read.return_value = b"not valid json"

    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = lambda s, *a: False

    with patch('update_checker.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value = mock_response

        checker = UpdateChecker("1.1.8")
        update_available, version, url, notes = checker.check_for_update()

        assert update_available is False, "Should return False on invalid JSON"
        print("  ✓ Handles invalid JSON gracefully")


def test_latest_version_property():
    """Test latest_version property"""
    checker = UpdateChecker("1.0.0")
    assert checker.latest_version == "unknown", "Should be 'unknown' before check"
    print("  ✓ latest_version is 'unknown' before check")


def test_download_url_property():
    """Test download_url property"""
    checker = UpdateChecker("1.0.0")
    url = checker.download_url
    assert "github.com" in url, f"Expected github URL, got '{url}'"
    print(f"  ✓ download_url: {url}")


def test_check_for_updates_async():
    """Test async update checker calls callback with result"""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        'tag_name': '2.0.0',
        'html_url': 'https://github.com/wardbryan3/SeleniumDownloader/releases/tag/2.0.0',
        'body': ''
    }).encode('utf-8')

    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = lambda s, *a: False

    callback_results = []

    def test_callback(result):
        callback_results.append(result)

    with patch('update_checker.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value = mock_response

        from update_checker import check_for_updates_async
        import time
        check_for_updates_async("1.1.8", test_callback)

        time.sleep(1)

        assert len(callback_results) == 1, "Callback should be called once"
        result = callback_results[0]
        assert result[0] is True, "Should detect update"
        assert result[1] == "2.0.0", f"Expected '2.0.0', got '{result[1]}'"
        print("  ✓ Async checker calls callback with correct result")


def run_tests():
    """Run all update_checker tests"""
    print("=" * 60)
    print("Running Update Checker Tests")
    print("=" * 60)

    tests = [
        test_parse_version_valid,
        test_parse_version_invalid,
        test_parse_version_none,
        test_check_for_update_newer_available,
        test_check_for_update_current_is_latest,
        test_check_for_update_network_error,
        test_check_for_update_invalid_json,
        test_latest_version_property,
        test_download_url_property,
        test_check_for_updates_async,
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
