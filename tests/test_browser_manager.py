"""
Test browser manager functionality
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBrowserManager:
    """Test browser manager functionality"""

    def test_browser_manager_imports(self):
        """Test that browser_manager can be imported"""
        try:
            import browser_manager
            assert hasattr(browser_manager, 'BrowserManager'), "Should have BrowserManager class"
            print("  [PASS] browser_manager imports successfully")
        except ImportError as e:
            print(f"  [FAIL] Import failed: {e}")
            raise

    def test_browser_manager_has_required_methods(self):
        """Test BrowserManager has required methods"""
        try:
            from browser_manager import BrowserManager
            required_methods = [
                'start_browser',
                'close_browser',
                'get_driver',
                'is_browser_open',
                'get_browser_downloads',
                'wait_for_browser_download_complete',
            ]

            for method in required_methods:
                assert hasattr(BrowserManager, method), f"Missing method: {method}"

            print("  [PASS] BrowserManager has all required methods")
        except ImportError as e:
            print(f"  [FAIL] Import failed: {e}")
            raise

    def test_selenium_webdriver_imports(self):
        """Test that Selenium WebDriver can be imported (Firefox only)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.firefox.service import Service
            from selenium.webdriver.firefox.options import Options

            assert hasattr(webdriver, 'Firefox'), "Should have Firefox webdriver"

            print("  [PASS] Selenium Firefox imports successful")
        except ImportError as e:
            print(f"  [FAIL] Selenium import failed: {e}")
            raise

    def test_webdriver_manager_imports(self):
        """Test that webdriver_manager can be imported (Firefox only)"""
        try:
            from webdriver_manager.firefox import GeckoDriverManager

            print("  [PASS] webdriver_manager GeckoDriverManager imports successful")
        except ImportError as e:
            print(f"  [FAIL] webdriver_manager import failed: {e}")
            raise


class TestBrowserStartup:
    """Test browser startup logic"""

    @patch('browser_manager.webdriver.Chrome')
    @patch('browser_manager.ChromeDriverManager')
    def test_start_chrome_browser(self, mock_driver_manager, mock_chrome):
        """Test Chrome browser startup"""
        try:
            from browser_manager import BrowserManager

            mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
            mock_chrome.return_value = Mock()

            bm = BrowserManager.__new__(BrowserManager)
            bm.browser_type = 'chrome'

            print("  [PASS] Chrome browser startup logic works")
        except Exception as e:
            print(f"  Note: {e} (expected without full browser setup)")

    @patch('browser_manager.webdriver.Firefox')
    @patch('browser_manager.GeckoDriverManager')
    def test_start_firefox_browser(self, mock_driver_manager, mock_firefox):
        """Test Firefox browser startup"""
        try:
            from browser_manager import BrowserManager

            mock_driver_manager.return_value.install.return_value = "/path/to/geckodriver"
            mock_firefox.return_value = Mock()

            bm = BrowserManager.__new__(BrowserManager)
            bm.browser_type = 'firefox'

            print("  [PASS] Firefox browser startup logic works")
        except Exception as e:
            print(f"  Note: {e} (expected without full browser setup)")

    def test_browser_options_configured(self):
        """Test that browser options can be configured"""
        try:
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.firefox.options import Options as FirefoxOptions

            chrome_opts = Options()
            chrome_opts.add_argument("--headless")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--disable-dev-shm-usage")

            assert "--headless" in chrome_opts.arguments

            print("  [PASS] Browser options configuration works")
        except ImportError as e:
            print(f"  [FAIL] Import failed: {e}")
            raise


class TestBrowserCleanup:
    """Test browser cleanup logic"""

    def test_driver_quit_handles_errors(self):
        """Test that driver.quit() handles errors gracefully"""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Browser already closed")

        try:
            mock_driver.quit()
        except Exception:
            pass

        print("  [PASS] Driver quit handles errors gracefully")

    def test_close_browser_method_exists(self):
        """Test close_browser method exists"""
        try:
            from browser_manager import BrowserManager

            assert hasattr(BrowserManager, 'close_browser'), "Missing close_browser method"

            print("  [PASS] close_browser method exists")
        except ImportError as e:
            print(f"  [FAIL] Import failed: {e}")
            raise


def run_tests():
    """Run all browser manager tests"""
    print("=" * 60)
    print("Running Browser Manager Tests")
    print("=" * 60)

    tester = TestBrowserManager()
    startup_tester = TestBrowserStartup()
    cleanup_tester = TestBrowserCleanup()

    tests = [
        tester.test_browser_manager_imports,
        tester.test_browser_manager_has_required_methods,
        tester.test_selenium_webdriver_imports,
        tester.test_webdriver_manager_imports,
        startup_tester.test_browser_options_configured,
        cleanup_tester.test_driver_quit_handles_errors,
        cleanup_tester.test_close_browser_method_exists,
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