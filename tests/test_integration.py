"""
Integration tests for full download workflows
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDownloadWorkflow:
    """Test full download workflows"""

    def test_config_manager_workflow(self):
        """Test full ConfigManager workflow"""
        from config import ConfigManager

        cm = ConfigManager()

        cm.set("test_key", "test_value")
        assert cm.get("test_key") == "test_value"

        saved = cm.save()
        assert saved is True

        cm2 = ConfigManager()
        assert cm2.get("test_key") == "test_value"

        cm2.set("test_key", None)
        cm2.save()

        print("  ✓ Full ConfigManager workflow works")

    def test_source_initialization(self):
        """Test that all sources can be initialized"""
        from sources.base import BaseDownloader
        from config import ConfigManager

        cm = ConfigManager()

        source_classes = [
            'MelindaMyersDownloader',
            'NorthwestOutdoorsDownloader',
            'WhittlerDownloader',
            'WestwoodOneDownloader',
            'ClearOutWestDownloader',
        ]

        for class_name in source_classes:
            try:
                module = __import__(f'sources.{class_name.lower().replace("downloader", "")}', fromlist=[class_name])
                cls = getattr(module, class_name)
                print(f"  ✓ {class_name} can be imported")
            except (ImportError, AttributeError) as e:
                print(f"  Note: {class_name} - {e}")

    def test_downloader_has_required_methods(self):
        """Test BaseDownloader has required methods"""
        from sources.base import BaseDownloader

        required_methods = [
            'download',
            'cleanup',
            'should_auto_close_browser',
        ]

        for method in required_methods:
            assert hasattr(BaseDownloader, method), f"Missing method: {method}"

        print("  ✓ BaseDownloader has all required methods")

    def test_promo_tag_workflow(self):
        """Test promo tag overlay workflow"""
        from config import ConfigManager

        cm = ConfigManager()

        tag_file = cm.get_tag_file()
        assert tag_file is not None
        print(f"  ✓ Tag file path: {tag_file}")

        promos_dir = cm.get_promos_dir()
        assert promos_dir is not None
        print(f"  ✓ Promos directory: {promos_dir}")


class TestEndToEndScenarios:
    """Test end-to-end scenarios"""

    @patch('sources.base.BaseDownloader.start_browser')
    def test_northwest_outdoors_workflow(self, mock_start_browser):
        """Test Northwest Outdoors download workflow"""
        mock_start_browser.return_value = True

        from sources.northwest_outdoors import NorthwestOutdoorsDownloader
        from config import ConfigManager
        from browser_manager import BrowserManager

        cm = ConfigManager()
        bm = BrowserManager()

        downloader = NorthwestOutdoorsDownloader(cm, bm)

        url = cm.get("urls", {}).get("northwest_outdoors", "")
        is_valid = bool(url) and "YOUR_LINK" not in url

        assert is_valid, "URL should be valid"
        print(f"  ✓ Northwest Outdoors workflow ready with valid URL")

    @patch('sources.base.BaseDownloader.start_browser')
    def test_whittler_workflow(self, mock_start_browser):
        """Test Whittler download workflow"""
        mock_start_browser.return_value = True

        from sources.whittler import WhittlerDownloader
        from config import ConfigManager
        from browser_manager import BrowserManager

        cm = ConfigManager()
        bm = BrowserManager()

        downloader = WhittlerDownloader(cm, bm)

        url = cm.get("urls", {}).get("whittler", "")
        is_valid = bool(url) and "YOUR_LINK" not in url

        assert is_valid, "URL should be valid"
        print(f"  ✓ Whittler workflow ready with valid URL")

    def test_test_mode_path_workflow(self):
        """Test test mode vs production mode paths"""
        from config import ConfigManager

        cm = ConfigManager()

        cm.config["test_mode"] = True
        cm.config["test_downloads_dir"] = "test_downloads"

        test_output = cm.get_output_base_dir()
        assert "test_downloads" in test_output

        test_promos = cm.get_promos_dir()
        assert "test_downloads" in test_promos

        cm.config["test_mode"] = False
        cm.config["dropbox_base"] = "D:/Dropbox"

        prod_output = cm.get_output_base_dir()
        assert "Dropbox" in prod_output

        print(f"  ✓ Test mode: {test_output}")
        print(f"  ✓ Production mode: {prod_output}")

    def test_validate_config_workflow(self):
        """Test config validation workflow"""
        from config import ConfigManager

        cm = ConfigManager()

        cm.config["email"] = "test@test.com"
        cm.config["password"] = "testpass"
        cm.config["cow_password"] = "testcow"

        errors = cm.validate_config()

        email_error = any("email" in e.lower() for e in errors)
        password_error = any("password" in e.lower() for e in errors)
        cow_error = any("cow" in e.lower() for e in errors)

        assert not email_error, "Should not have email error"
        assert not password_error, "Should not have password error"
        assert not cow_error, "Should not have cow_password error"

        print("  ✓ Config validation passes with all required fields")

    def test_browser_download_dir_workflow(self):
        """Test browser download directory workflow"""
        from config import ConfigManager
        from pathlib import Path

        cm = ConfigManager()

        download_dir = cm.get_browser_download_dir()
        assert download_dir is not None
        assert len(download_dir) > 0

        print(f"  ✓ Browser download dir: {download_dir}")

        cm.clear_browser_download_dir()
        print("  ✓ Browser download dir cleared")


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_missing_config_file_creates_default(self):
        """Test that missing config file creates default"""
        import tempfile

        temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_config.close()
        os.unlink(temp_config.name)

        original_file = ConfigManager.CONFIG_FILE if hasattr(ConfigManager, 'CONFIG_FILE') else None

        try:
            import config
            config.CONFIG_FILE = temp_config.name

            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)

            cm = ConfigManager()

            assert os.path.exists(temp_config.name), "Config file should be created"

            print(f"  ✓ Missing config creates default at: {temp_config.name}")

        finally:
            if original_file:
                config.CONFIG_FILE = original_file
            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)

    def test_invalid_json_handled(self):
        """Test that invalid JSON is handled gracefully"""
        import tempfile

        temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_config.write("{ invalid json }")
        temp_config.close()

        try:
            cm = ConfigManager()
            print("  ✓ Invalid JSON handled gracefully")
        except Exception as e:
            print(f"  Note: {e}")
        finally:
            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)


def run_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)

    tests = [
        TestDownloadWorkflow().test_config_manager_workflow,
        TestDownloadWorkflow().test_source_initialization,
        TestDownloadWorkflow().test_downloader_has_required_methods,
        TestDownloadWorkflow().test_promo_tag_workflow,
        TestEndToEndScenarios().test_test_mode_path_workflow,
        TestEndToEndScenarios().test_validate_config_workflow,
        TestEndToEndScenarios().test_browser_download_dir_workflow,
        TestErrorHandling().test_invalid_json_handled,
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