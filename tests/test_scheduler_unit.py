"""
Unit tests for scheduler.py - test DownloadScheduler directly
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler import DownloadScheduler
from config import ConfigManager, DAY_MAPPING


def test_scheduler_init():
    """Test DownloadScheduler initializes correctly"""
    cm = ConfigManager()
    callback = MagicMock()

    scheduler = DownloadScheduler(cm, callback)

    assert scheduler.config_manager is cm, "Config manager should be stored"
    assert scheduler.download_callback is callback, "Callback should be stored"
    assert scheduler.running is False, "Should not be running initially"
    assert scheduler.jobs == [], "Jobs should start empty"
    assert scheduler.thread is None, "Thread should be None initially"
    print("  [PASS] DownloadScheduler initializes correctly")


def test_scheduler_start_stop():
    """Test start() and stop() lifecycle"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    scheduler.start()
    assert scheduler.running is True, "Should be running after start"
    assert scheduler.thread is not None, "Thread should be created"
    assert scheduler.thread.is_alive(), "Thread should be alive"

    scheduler.stop()
    time.sleep(0.1)  # Give thread time to stop
    assert scheduler.running is False, "Should not be running after stop"
    print("  [PASS] start()/stop() lifecycle works")


def test_scheduler_start_already_running():
    """Test start() does nothing if already running"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    scheduler.start()
    original_thread = scheduler.thread

    scheduler.start()  # Call start again
    assert scheduler.thread is original_thread, "Should not create new thread"
    scheduler.stop()
    print("  [PASS] start() is no-op when already running")


def test_update_from_config_disabled():
    """Test update_from_config with disabled scheduler"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    # Set config to disabled
    cm.set("scheduled_downloads", {"enabled": False})
    scheduler.update_from_config()

    assert len(scheduler.jobs) == 0, "No jobs should be added when disabled"
    print("  [PASS] No jobs added when scheduler disabled")


def test_update_from_config_daily():
    """Test update_from_config creates daily job"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "daily",
        "time": "06:00",
        "days": [],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    assert len(scheduler.jobs) == 1, f"Should have 1 job, got {len(scheduler.jobs)}"
    job = scheduler.jobs[0]
    assert job['type'] == "daily", f"Job type should be daily, got {job['type']}"
    assert job['time'] == "06:00", f"Job time should be 06:00, got {job['time']}"
    assert job['last_run'] is None, "last_run should be None initially"
    print("  [PASS] Daily job created from config")


def test_update_from_config_weekly():
    """Test update_from_config creates weekly job with day mapping"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "weekly",
        "time": "12:30",
        "days": ["Monday", "Friday"],
        "download_all": False,
        "selected_sources": ["Melinda Myers"]
    })
    scheduler.update_from_config()

    assert len(scheduler.jobs) == 1, "Should have 1 job"
    job = scheduler.jobs[0]
    assert job['type'] == "weekly", "Job type should be weekly"
    assert "Mon" in job['days'], f"Should have Mon in days, got {job['days']}"
    assert "Fri" in job['days'], f"Should have Fri in days, got {job['days']}"
    print(f"  [PASS] Weekly job created with days: {job['days']}")


def test_update_from_config_invalid_time():
    """Test update_from_config handles invalid time format"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "daily",
        "time": "25:99",  # Invalid time
        "days": [],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    # Should fall back to 06:00
    assert len(scheduler.jobs) == 1, "Should still create job"
    assert scheduler.jobs[0]['time'] == "06:00", "Should fall back to 06:00"
    print("  [PASS] Invalid time falls back to 06:00")


def test_run_pending_disabled():
    """Test run_pending does nothing when disabled"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    # Scheduler disabled
    cm.set("scheduled_downloads", {"enabled": False})
    scheduler.update_from_config()

    scheduler.run_pending()
    callback.assert_not_called(), "Callback should not be called when disabled"
    print("  [PASS] run_pending does nothing when disabled")


def test_run_pending_time_match_daily():
    """Test run_pending fires daily job at correct time"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    # Set up daily job at current time
    now = datetime.now()
    current_time = now.strftime('%H:%M')

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "daily",
        "time": current_time,
        "days": [],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    # Should run because time matches
    scheduler.run_pending()
    callback.assert_called_once()
    print("  [PASS] Daily job fires when time matches")


def test_run_pending_time_mismatch():
    """Test run_pending does not fire when time doesn't match"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    # Set time to something different
    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "daily",
        "time": "00:00",  # Unlikely to be current time
        "days": [],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    scheduler.run_pending()
    callback.assert_not_called(), "Callback should not be called when time doesn't match"
    print("  [PASS] Job doesn't fire when time doesn't match")


def test_run_pending_weekly_day_match():
    """Test run_pending fires weekly job on correct day"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    now = datetime.now()
    current_time = now.strftime('%H:%M')
    current_day = now.strftime('%a')  # e.g., "Mon"

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "weekly",
        "time": current_time,
        "days": [now.strftime('%A')],  # Full day name, e.g., "Monday"
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    scheduler.run_pending()
    callback.assert_called_once()
    print(f"  [PASS] Weekly job fires on correct day ({current_day})")


def test_run_pending_weekly_day_mismatch():
    """Test run_pending doesn't fire weekly job on wrong day"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    now = datetime.now()
    current_time = now.strftime('%H:%M')

    # Pick a day that's NOT today
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = now.strftime('%A')
    wrong_day = [d for d in days if d != today][0]

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "weekly",
        "time": current_time,
        "days": [wrong_day],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    scheduler.run_pending()
    callback.assert_not_called(), "Callback should not fire on wrong day"
    print(f"  [PASS] Weekly job doesn't fire on wrong day (today: {today}, scheduled: {wrong_day})")


def test_run_pending_no_double_run():
    """Test run_pending doesn't run same job twice in same minute"""
    cm = ConfigManager()
    callback = MagicMock()
    scheduler = DownloadScheduler(cm, callback)

    now = datetime.now()
    current_time = now.strftime('%H:%M')

    cm.set("scheduled_downloads", {
        "enabled": True,
        "schedule_type": "daily",
        "time": current_time,
        "days": [],
        "download_all": True,
        "selected_sources": []
    })
    scheduler.update_from_config()

    # First call should fire
    scheduler.run_pending()
    assert scheduler.jobs[0]['last_run'] is not None, "last_run should be set"

    # Reset callback mock and call again
    callback.reset_mock()
    scheduler.run_pending()
    callback.assert_not_called(), "Should not fire again in same minute"
    print("  [PASS] Job doesn't fire twice in same minute")


def run_tests():
    """Run all scheduler unit tests"""
    print("=" * 60)
    print("Running Scheduler Unit Tests")
    print("=" * 60)

    tests = [
        test_scheduler_init,
        test_scheduler_start_stop,
        test_scheduler_start_already_running,
        test_update_from_config_disabled,
        test_update_from_config_daily,
        test_update_from_config_weekly,
        test_update_from_config_invalid_time,
        test_run_pending_disabled,
        test_run_pending_time_match_daily,
        test_run_pending_time_mismatch,
        test_run_pending_weekly_day_match,
        test_run_pending_weekly_day_mismatch,
        test_run_pending_no_double_run,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            # Reset scheduler state between tests
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
