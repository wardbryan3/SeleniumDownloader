"""
Unit tests for browser_manager.py - mock Selenium to test logic
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock selenium and webdriver_manager if not installed
try:
    from config import ConfigManager
except ImportError:
    # Mock the selenium imports that browser_manager uses
    import unittest.mock as mock
    sys.modules['selenium'] = MagicMock()
    sys.modules['selenium.webdriver'] = MagicMock()
    sys.modules['selenium.webdriver.firefox'] = MagicMock()
    sys.modules['selenium.webdriver.firefox.service'] = MagicMock()
    sys.modules['selenium.webdriver.firefox.options'] = MagicMock()
    sys.modules['selenium.webdriver.support'] = MagicMock()
    sys.modules['selenium.webdriver.support.ui'] = MagicMock()
    sys.modules['selenium.webdriver.support.expected_conditions'] = MagicMock()
    sys.modules['selenium.common'] = MagicMock()
    sys.modules['selenium.common.exceptions'] = MagicMock()
    sys.modules['webdriver_manager'] = MagicMock()
    sys.modules['webdriver_manager.firefox'] = MagicMock()
    from config import ConfigManager


def test_browser_manager_init():
    """Test BrowserManager initializes with config"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    assert bm.config_manager is cm, "Config manager should be stored"
    assert bm.driver is None, "Driver should start as None"
    print("  [PASS] BrowserManager initializes correctly")


def test_create_browser_options():
    """Test _create_browser_options returns correct Firefox prefs"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    options = bm._create_browser_options()

    assert options is not None, "Options should be created"
    assert hasattr(options, 'preferences') or hasattr(options, '_preferences'), "Options should have preferences"

    prefs = options.preferences if hasattr(options, 'preferences') else options._preferences
    assert prefs.get("browser.download.folderList") == 2, "Should set download folderList to 2"
    assert "neverAsk.saveToDisk" in str(prefs), "Should set neverAsk.saveToDisk"
    print("  [PASS] Firefox options configured correctly")


@patch('browser_manager.GeckoDriverManager')
@patch('browser_manager.webdriver.Firefox')
def test_start_browser_success(mock_firefox, mock_gecko):
    """Test start_browser sets driver on success"""
    mock_driver = MagicMock()
    mock_firefox.return_value = mock_driver
    mock_gecko.return_value.install.return_value = "/path/to/geckodriver"

    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    result = bm.start_browser()

    assert result is True, "start_browser should return True on success"
    assert bm.driver is mock_driver, "Driver should be set after start"
    mock_firefox.assert_called_once()
    print("  [PASS] start_browser succeeds and sets driver")


@patch('browser_manager.GeckoDriverManager')
@patch('browser_manager.webdriver.Firefox')
def test_start_browser_already_running(mock_firefox, mock_gecko):
    """Test start_browser returns True if already running"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    bm.driver = MagicMock()

    result = bm.start_browser()

    assert result is True, "Should return True when already running"
    mock_firefox.assert_not_called(), "Should not create new driver"
    print("  [PASS] start_browser returns True when already running")


@patch('browser_manager.GeckoDriverManager')
@patch('browser_manager.webdriver.Firefox')
def test_start_browser_failure(mock_firefox, mock_gecko):
    """Test start_browser returns False on exception"""
    mock_firefox.side_effect = Exception("Browser failed to start")

    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    result = bm.start_browser()

    assert result is False, "Should return False on failure"
    assert bm.driver is None, "Driver should be None on failure"
    print("  [PASS] start_browser returns False on failure")


def test_close_browser():
    """Test close_browser quits driver and sets to None"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    mock_driver = MagicMock()
    bm.driver = mock_driver

    bm.close_browser()

    mock_driver.quit.assert_called_once()
    assert bm.driver is None, "Driver should be None after close"
    print("  [PASS] close_browser quits driver and clears it")


def test_close_browser_when_none():
    """Test close_browser handles None driver gracefully"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    bm.driver = None

    try:
        bm.close_browser()
        print("  [PASS] close_browser handles None driver")
    except Exception as e:
        print(f"  [FAIL] close_browser raised exception: {e}")


def test_get_driver_auto_start():
    """Test get_driver auto-starts browser if not running"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    assert bm.driver is None, "Driver should start as None"

    with patch.object(bm, 'start_browser', return_value=True) as mock_start:
        result = bm.get_driver()
        mock_start.assert_called_once()
        print("  [PASS] get_driver auto-starts browser")


def test_get_driver_returns_existing():
    """Test get_driver returns existing driver without starting"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    mock_driver = MagicMock()
    bm.driver = mock_driver

    with patch.object(bm, 'start_browser') as mock_start:
        result = bm.get_driver()
        mock_start.assert_not_called()
        assert result is mock_driver, "Should return existing driver"
        print("  [PASS] get_driver returns existing driver")


def test_is_browser_open():
    """Test is_browser_open returns correct state"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    assert bm.is_browser_open() is False, "Should be False when no driver"

    bm.driver = MagicMock()
    assert bm.is_browser_open() is True, "Should be True when driver exists"

    bm.driver = None
    assert bm.is_browser_open() is False, "Should be False after clearing driver"
    print("  [PASS] is_browser_open returns correct state")


@patch('browser_manager.webdriver.Firefox')
def test_get_browser_downloads(mock_firefox):
    """Test get_browser_downloads with mocked driver"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    mock_driver = MagicMock()
    bm.driver = mock_driver

    # Mock WebDriverWait and execute_script
    with patch('browser_manager.WebDriverWait') as mock_wait:
        mock_wait.return_value.until.return_value = True

        # Simulate JavaScript returning download items
        mock_driver.execute_script.return_value = [
            {'name': 'test.mp3', 'state': 'complete', 'progress': 100},
            {'name': 'test2.zip', 'state': '', 'progress': 100},
        ]

        downloads = bm.get_browser_downloads(timeout=1)

        assert len(downloads) == 2, f"Expected 2 downloads, got {len(downloads)}"
        assert downloads[0]['name'] == 'test.mp3'
        print("  [PASS] get_browser_downloads returns parsed downloads")


def test_get_browser_downloads_no_driver():
    """Test get_browser_downloads returns empty list when no driver"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    bm.driver = None

    downloads = bm.get_browser_downloads()
    assert downloads == [], "Should return empty list when no driver"
    print("  [PASS] get_browser_downloads returns empty when no driver")


@patch('browser_manager.webdriver.Firefox')
def test_wait_for_browser_download_complete_timeout(mock_firefox):
    """Test wait_for_browser_download_complete times out"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    bm.driver = MagicMock()

    with patch.object(bm, 'get_browser_downloads', return_value=[]):
        result = bm.wait_for_browser_download_complete(timeout=1, poll_interval=0.1)
        assert result is None, "Should return None on timeout"
        print("  [PASS] wait_for_browser_download_complete handles timeout")


@patch('browser_manager.webdriver.Firefox')
def test_wait_for_browser_download_complete_finds_file(mock_firefox):
    """Test wait_for_browser_download_complete returns file path"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)
    bm.driver = MagicMock()

    # Create a fake download in the browser download dir
    download_dir = Path(cm.get_browser_download_dir())
    download_dir.mkdir(parents=True, exist_ok=True)
    test_file = download_dir / "test.mp3"
    test_file.write_bytes(b"fake audio")

    try:
        with patch.object(bm, 'get_browser_downloads', return_value=[
            {'name': 'test.mp3', 'state': 'complete', 'progress': 100}
        ]):
            result = bm.wait_for_browser_download_complete(timeout=2, poll_interval=0.1)
            assert result is not None, "Should find the download"
            assert "test.mp3" in result, f"Should return file path, got {result}"
            print("  [PASS] wait_for_browser_download_complete finds file")
    finally:
        if test_file.exists():
            test_file.unlink()


def test_initialize_download_directory():
    """Test _initialize_download_directory creates the directory"""
    cm = ConfigManager()
    from browser_manager import BrowserManager
    bm = BrowserManager(cm)

    download_dir = Path(bm._get_temp_download_dir())
    assert download_dir.exists(), "Download directory should be created"
    print(f"  [PASS] Download directory exists: {download_dir}")


def run_tests():
    """Run all browser manager unit tests"""
    print("=" * 60)
    print("Running Browser Manager Unit Tests")
    print("=" * 60)

    tests = [
        test_browser_manager_init,
        test_create_browser_options,
        test_start_browser_success,
        test_start_browser_already_running,
        test_start_browser_failure,
        test_close_browser,
        test_close_browser_when_none,
        test_get_driver_auto_start,
        test_get_driver_returns_existing,
        test_is_browser_open,
        test_get_browser_downloads,
        test_get_browser_downloads_no_driver,
        test_wait_for_browser_download_complete_timeout,
        test_wait_for_browser_download_complete_finds_file,
        test_initialize_download_directory,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
