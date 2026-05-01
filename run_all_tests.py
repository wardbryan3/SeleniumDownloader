"""
Run all test files in the project.
Usage: .venv/bin/python3 run_all_tests.py
"""

import sys
import subprocess
from pathlib import Path

# All test files to run
TEST_FILES = [
    "test_downloads.py",
    "test_detection_standalone.py",
    "tests/test_config_edge_cases.py",
    "tests/test_integration.py",
    "tests/test_scheduler.py",
    "tests/test_scheduler_unit.py",
    "tests/test_browser_manager.py",
    "tests/test_browser_manager_unit.py",
    "tests/test_sources.py",
    "tests/test_sources_unit.py",
    "tests/test_download_utils.py",
    "tests/test_update_checker.py",
    "tests/test_config_unit.py",
]

def main():
    project_root = Path(__file__).parent
    failed = 0
    results = []

    print("=" * 60)
    print("Running All Tests")
    print("=" * 60)
    print()

    for test_file in TEST_FILES:
        test_path = project_root / test_file
        if not test_path.exists():
            print(f"  SKIP (not found): {test_file}")
            continue

        print(f"Running: {test_file}...")
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=False,
            cwd=str(project_root)
        )

        if result.returncode == 0:
            print(f"  ✓ PASSED: {test_file}")
            results.append((test_file, "PASSED"))
        else:
            print(f"  ✗ FAILED: {test_file} (exit code: {result.returncode})")
            results.append((test_file, "FAILED"))
            failed += 1
        print()

    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    for test_file, status in results:
        marker = "✓" if status == "PASSED" else "✗"
        print(f"  {marker} {test_file}: {status}")

    print()
    print(f"Total: {len(results)} tests, {len(results) - failed} passed, {failed} failed")

    if failed > 0:
        print()
        print("Some tests FAILED!")
        sys.exit(1)
    else:
        print()
        print("All tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
