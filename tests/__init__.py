"""
Test suite for Audio Download Manager
Run with: python -m pytest tests/ -v
        or: python test_config.py (standalone tests)
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager, DEFAULT_CONFIG, CONFIG_FILE

def test_set_method():
    """Test that set() method works"""
    print("Testing set() method...")
    cm = ConfigManager()
    cm.set("test_key", "test_value")
    assert cm.get("test_key") == "test_value", "set() failed"
    print("  ✓ set() works")

def test_save_method():
    """Test that save() method works"""
    print("Testing save() method...")
    cm = ConfigManager()
    test_value = f"test_save_{os.urandom(4).hex()}"
    cm.set("test_save_key", test_value)
    result = cm.save()
    assert result is True, "save() returned False"
    assert cm.get("test_save_key") == test_value, "save() didn't persist value"
    print("  ✓ save() works")

def test_url_config():
    """Test that URLs load from config"""
    print("Testing URL config...")
    cm = ConfigManager()
    urls = cm.get("urls", {})
    assert "northwest_outdoors" in urls, "northwest_outdoors URL key missing"
    assert "whittler" in urls, "whittler URL key missing"
    print(f"  ✓ northwest_outdoors URL: {urls.get('northwest_outdoors')}")
    print(f"  ✓ whittler URL: {urls.get('whittler')}")

def test_cow_password_default():
    """Test that cow_password defaults to empty string"""
    print("Testing cow_password default...")
    assert DEFAULT_CONFIG.get("cow_password") == "", f"cow_password should be empty"
    print("  ✓ cow_password defaults to empty string")

def test_url_validation():
    """Test URL validation in DEFAULT_CONFIG"""
    print("Testing URL validation in DEFAULT_CONFIG...")
    urls = DEFAULT_CONFIG.get("urls", {})
    assert "YOUR_LINK" in urls.get("northwest_outdoors", ""), "Placeholder URL should be in default"
    assert "YOUR_LINK" in urls.get("whittler", ""), "Placeholder URL should be in default"
    print("  ✓ Placeholder URLs in DEFAULT_CONFIG detected correctly")

def main():
    print("=" * 50)
    print("Running ConfigManager Tests")
    print("=" * 50)

    try:
        test_set_method()
        test_save_method()
        test_url_config()
        test_cow_password_default()
        test_url_validation()

        print("=" * 50)
        print("All tests passed!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())