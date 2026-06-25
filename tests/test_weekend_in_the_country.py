"""
Tests for Weekend In The Country downloader (rename logic and promo selection)
"""

import sys
import re
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_file(dir_path, name):
    """Create an empty file in dir_path"""
    (dir_path / name).touch()


def _simulate_process_files(output_dir):
    """Replicate the rename logic from weekend_in_the_country.py"""
    seg_re = re.compile(r'hr(\d+)_seg(\d+)', re.IGNORECASE)
    date_re = re.compile(r'(\d{2}-\d{2}-\d{2})')
    promos = []
    segments = []

    for f in output_dir.iterdir():
        if not f.is_file() or not f.name.lower().endswith('.mp3'):
            continue
        if not f.name.startswith('Weekend in the Country'):
            continue

        name = f.name
        seg_match = seg_re.search(name)
        if seg_match:
            segments.append((f, seg_match.group(1), seg_match.group(2)))
            continue

        if 'promo' in name.lower():
            date_match = date_re.search(name)
            promos.append((f, date_match.group(1) if date_match else ''))

    for f, hr, pt in segments:
        new_name = f.parent / f"WITC_HR{hr}_PT{pt}.mp3"
        f.rename(new_name)

    for f, date_str in promos:
        date_tag = f"_{date_str}" if date_str else ""
        new_name = f.parent / f"WITC_PROMO{date_tag}.mp3"
        f.rename(new_name)


def test_segments_renamed_correctly():
    """Segment files are renamed to WITC_HR{num}_PT{num}"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-27-26_hr1_seg1.mp3")
        _make_file(tmp, "Weekend in the Country_06-27-26_hr1_seg2.mp3")
        _make_file(tmp, "Weekend in the Country_06-27-26_hr2_seg1.mp3")
        _make_file(tmp, "Weekend in the Country_06-27-26_hr2_seg4.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        expected = {"WITC_HR1_PT1.mp3", "WITC_HR1_PT2.mp3",
                     "WITC_HR2_PT1.mp3", "WITC_HR2_PT4.mp3"}
        assert files == expected, f"Got {files}"
        print("  ✓ Segments renamed correctly")
    finally:
        shutil.rmtree(tmp)


def test_no_segments_skipped():
    """Files without hr/seg pattern are left untouched"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-27-26_hr1_seg1.mp3")
        _make_file(tmp, "some_other_file.mp3")

        _simulate_process_files(tmp)

        names = {f.name for f in tmp.iterdir() if f.is_file()}
        assert "WITC_HR1_PT1.mp3" in names
        assert "some_other_file.mp3" in names
        print("  ✓ Non-WITC files left untouched")
    finally:
        shutil.rmtree(tmp)


def test_promos_renamed_with_date():
    """Each promo is renamed to WITC_PROMO_MM-DD-YY.mp3"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-27-26 promo.mp3")
        _make_file(tmp, "Weekend in the Country_07-04-26 promo.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert "WITC_PROMO_06-27-26.mp3" in files, "First promo missing"
        assert "WITC_PROMO_07-04-26.mp3" in files, "Second promo missing"
        assert "Weekend in the Country_06-27-26 promo.mp3" not in files, \
            "Original should be renamed"
        print("  ✓ Both promos renamed with date tags")
    finally:
        shutil.rmtree(tmp)


def test_promo_without_date_defaults():
    """Promo with unparseable date is renamed without tag"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_baddate promo.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert "WITC_PROMO.mp3" in files, "Promo with bad date should still be kept"
        print("  ✓ Promo with unparseable date handled")
    finally:
        shutil.rmtree(tmp)


def test_single_promo_kept():
    """Single promo is renamed with date"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-27-26 promo.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert files == {"WITC_PROMO_06-27-26.mp3"}, f"Got {files}"
        print("  ✓ Single promo renamed with date")
    finally:
        shutil.rmtree(tmp)


def test_no_promo_no_error():
    """No promo files is handled gracefully"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-27-26_hr1_seg1.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert files == {"WITC_HR1_PT1.mp3"}, f"Got {files}"
        print("  ✓ No promo files handled gracefully")
    finally:
        shutil.rmtree(tmp)


def test_non_weekend_files_ignored():
    """Files not starting with 'Weekend in the Country' are ignored"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "completely_different.mp3")
        _make_file(tmp, "Weekend in the Country_06-27-26_hr1_seg1.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert "WITC_HR1_PT1.mp3" in files
        assert "completely_different.mp3" in files
        print("  ✓ Non-WITC files ignored by rename logic")
    finally:
        shutil.rmtree(tmp)


def test_promo_with_past_date_handled():
    """Past-date promo is renamed with its date"""
    tmp = Path(tempfile.mkdtemp())
    try:
        _make_file(tmp, "Weekend in the Country_06-20-26 promo.mp3")

        _simulate_process_files(tmp)

        files = {f.name for f in tmp.iterdir() if f.is_file()}
        assert "WITC_PROMO_06-20-26.mp3" in files, "Past promo should be renamed with date"
        print("  ✓ Past-date promo renamed with date")
    finally:
        shutil.rmtree(tmp)


def run_tests():
    """Run all Weekend In The Country tests"""
    print("=" * 60)
    print("Running Weekend In The Country Tests")
    print("=" * 60)

    tests = [
        test_segments_renamed_correctly,
        test_no_segments_skipped,
        test_promos_renamed_with_date,
        test_promo_without_date_defaults,
        test_single_promo_kept,
        test_no_promo_no_error,
        test_non_weekend_files_ignored,
        test_promo_with_past_date_handled,
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
