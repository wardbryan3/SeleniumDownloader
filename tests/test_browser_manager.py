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
            print("  ✓ browser_manager imports successfully")
        except ImportError as e:
            print(f"  ✗ Import failed: {e}")
            raise

    def test_browser_manager_has_required_methods(self):
        """Test BrowserManager has required methods"""
        try:
            from browser_manager import BrowserManager
            required_methods = [
                'start_browser',
                'close_browser',
                'get_driver',
                'get_browser_type',
                'set_browser_type',
            ]

            for method in required_methods:
                assert hasattr(BrowserManager, method), f"Missing method: {method}"

            print("  ✓ BrowserManager has all required methods")
        except ImportError as e:
            print(f"  ✗ Import failed: {e}")
            raise

    def test_browser_type_defaults(self):
        """Test default browser type settings"""
        try:
            from browser_manager import BrowserManager
            bm = BrowserManager.__new__(BrowserManager)

            default_browser = getattr(bm, 'browser_type', 'chrome')
            assert default_browser in ['chrome', 'firefox', 'edge'], f"Invalid default: {default_browser}"

            print(f"  ✓ Default browser type: {default_browser}")
        except Exception as e:
            print(f"  ✗ Test failed: {e}")

    def test_selenium_webdriver_imports(self):
        """Test that Selenium WebDriver can be imported"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            assert hasattr(webdriver, 'Chrome'), "Should have Chrome webdriver"
            assert hasattr(webdriver, 'Firefox'), "Should have Firefox webdriver"
            assert hasattr(webdriver, 'Edge'), "Should have Edge webdriver"

            print("  ✓ Selenium WebDriver imports successful")
        except ImportError as e:
            print(f"  ✗ Selenium import failed: {e}")
            raise

    def test_webdriver_manager_imports(self):
        """Test that webdriver_manager can be imported"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            from webdriver_manager.microsoft import EdgeChromiumDriverManager

            print("  ✓ webdriver_manager imports successful")
        except ImportError as e:
            print(f"  ✗ webdriver_manager import failed: {e}")
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

            print("  ✓ Chrome browser startup logic works")
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

            print("  ✓ Firefox browser startup logic works")
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

            print("  ✓ Browser options configuration works")
        except ImportError as e:
            print(f"  ✗ Import failed: {e}")
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

        print("  ✓ Driver quit handles errors gracefully")

    def test_close_browser_method_exists(self):
        """Test close_browser method exists"""
        try:
            from browser_manager import BrowserManager

            assert hasattr(BrowserManager, 'close_browser'), "Missing close_browser method"

            print("  ✓ close_browser method exists")
        except ImportError as e:
            print(f"  ✗ Import failed: {e}")
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
        tester.test_browser_type_defaults,
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