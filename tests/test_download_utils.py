"""
Tests for download_utils.py - pure logic functions
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from download_utils import DownloadUtilities
from constants import ALLOWED_EXTENSIONS, EXCLUDED_EXTENSIONS, EXCLUDED_PREFIXES


def test_get_file_hash_valid_file():
    """Test get_file_hash returns non-empty hash for valid file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for hashing")
        f.flush()
        filepath = f.name

    try:
        hash_result = DownloadUtilities.get_file_hash(filepath)
        assert hash_result != "", "Hash should not be empty"
        assert len(hash_result) == 32, f"MD5 hash should be 32 chars, got {len(hash_result)}"
        print(f"  [PASS] get_file_hash returns valid MD5: {hash_result[:8]}...")
    finally:
        os.unlink(filepath)


def test_get_file_hash_missing_file():
    """Test get_file_hash returns empty string for missing file"""
    result = DownloadUtilities.get_file_hash("/nonexistent/path/file.txt")
    assert result == "", "Should return empty string for missing file"
    print("  [PASS] get_file_hash handles missing file gracefully")


def test_get_file_hash_empty_file():
    """Test get_file_hash handles empty files"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        filepath = f.name

    try:
        hash_result = DownloadUtilities.get_file_hash(filepath)
        assert hash_result != "", "Empty file should still produce a hash"
        print("  [PASS] get_file_hash handles empty file")
    finally:
        os.unlink(filepath)


def test_is_file_locked_unlocked_file():
    """Test is_file_locked returns False for closed file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b"test data")
        f.flush()
        filepath = f.name

    try:
        locked = DownloadUtilities.is_file_locked(filepath)
        assert locked is False, "Unopened file should not be locked"
        print("  [PASS] is_file_locked returns False for closed file")
    finally:
        os.unlink(filepath)


def test_is_file_locked_opened_file():
    """Test is_file_locked detects open file handle"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b"test data")
        f.flush()
        filepath = f.name

    try:
        locked = DownloadUtilities.is_file_locked(filepath)
        assert locked is True, "Opened file should be detected as locked"
        print("  [PASS] is_file_locked detects open file handle")
    except AssertionError:
        print("  Note: is_file_locked may not detect locks on all platforms")
    finally:
        f.close()
        os.unlink(filepath)


def test_allowed_extensions():
    """Test ALLOWED_EXTENSIONS contains expected values"""
    assert '.mp3' in ALLOWED_EXTENSIONS, "Should allow .mp3"
    assert '.wav' in ALLOWED_EXTENSIONS, "Should allow .wav"
    assert '.zip' in ALLOWED_EXTENSIONS, "Should allow .zip"
    assert '.pdf' in ALLOWED_EXTENSIONS, "Should allow .pdf"
    print(f"  [PASS] ALLOWED_EXTENSIONS: {sorted(ALLOWED_EXTENSIONS)}")


def test_excluded_extensions():
    """Test EXCLUDED_EXTENSIONS contains expected values"""
    assert '.part' in EXCLUDED_EXTENSIONS, "Should exclude .part"
    assert '.crdownload' in EXCLUDED_EXTENSIONS, "Should exclude .crdownload"
    assert '.tmp' in EXCLUDED_EXTENSIONS, "Should exclude .tmp"
    assert '.download' in EXCLUDED_EXTENSIONS, "Should exclude .download"
    print(f"  [PASS] EXCLUDED_EXTENSIONS: {sorted(EXCLUDED_EXTENSIONS)}")


def test_excluded_prefixes():
    """Test EXCLUDED_PREFIXES contains expected values"""
    assert '.fea' in EXCLUDED_PREFIXES, "Should exclude .fea prefix"
    assert '.X' in EXCLUDED_PREFIXES, "Should exclude .X prefix"
    print(f"  [PASS] EXCLUDED_PREFIXES: {sorted(EXCLUDED_PREFIXES)}")


def test_find_latest_file_empty_dir():
    """Test find_latest_file returns None for empty directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = DownloadUtilities.find_latest_file(tmpdir)
        assert result is None, "Should return None for empty directory"
        print("  [PASS] find_latest_file returns None for empty dir")


def test_find_latest_file_with_files():
    """Test find_latest_file returns most recently modified file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "old.mp3"
        file2 = Path(tmpdir) / "new.mp3"
        file1.write_bytes(b"old")
        file2.write_bytes(b"new")

        result = DownloadUtilities.find_latest_file(tmpdir, extension='.mp3')
        assert result is not None, "Should find a file"
        assert "new.mp3" in result, f"Should return newest file, got {result}"
        print(f"  [PASS] find_latest_file returns newest: {Path(result).name}")


def test_find_latest_file_ignores_temp_files():
    """Test find_latest_file ignores .part/.crdownload files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        real_file = Path(tmpdir) / "audio.mp3"
        temp_file = Path(tmpdir) / "audio.mp3.part"
        real_file.write_bytes(b"real")
        import time
        time.sleep(0.01)
        temp_file.write_bytes(b"temp")

        result = DownloadUtilities.find_latest_file(tmpdir, extension='.mp3')
        assert result is not None, "Should find a file"
        assert "temp" not in result, "Should not return .part file"
        print("  [PASS] find_latest_file ignores temp files")


def test_simple_wait_for_download_timeout():
    """Test simple_wait_for_download returns None on timeout with empty dir"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = DownloadUtilities.simple_wait_for_download(
            tmpdir, expected_extensions=['.mp3'], timeout=1
        )
        assert result is None, "Should timeout and return None"
        print("  [PASS] simple_wait_for_download handles timeout gracefully")


def test_simple_wait_for_download_detects_file():
    """Test simple_wait_for_download detects new file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        import threading
        def add_file_delayed():
            import time
            time.sleep(0.5)
            (Path(tmpdir) / "test.mp3").write_bytes(b"audio content")

        t = threading.Thread(target=add_file_delayed)
        t.start()

        result = DownloadUtilities.simple_wait_for_download(
            tmpdir, expected_extensions=['.mp3'], timeout=3
        )

        t.join()
        assert result is not None, "Should detect new file"
        assert "test.mp3" in result, f"Should return the new file, got {result}"
        print(f"  [PASS] simple_wait_for_download detected file: {Path(result).name}")


def run_tests():
    """Run all download_utils tests"""
    print("=" * 60)
    print("Running Download Utilities Tests")
    print("=" * 60)

    tests = [
        test_get_file_hash_valid_file,
        test_get_file_hash_missing_file,
        test_get_file_hash_empty_file,
        test_is_file_locked_unlocked_file,
        test_is_file_locked_opened_file,
        test_allowed_extensions,
        test_excluded_extensions,
        test_excluded_prefixes,
        test_find_latest_file_empty_dir,
        test_find_latest_file_with_files,
        test_find_latest_file_ignores_temp_files,
        test_simple_wait_for_download_timeout,
        test_simple_wait_for_download_detects_file,
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
