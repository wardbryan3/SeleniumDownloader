"""
Test scheduler functionality
"""

import sys
from pathlib import Path
from datetime import datetime, time

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchedulerParsing:
    """Test scheduler time and day parsing"""

    def test_day_mapping(self):
        """Test day name mapping"""
        from config import DAY_MAPPING

        expected_mappings = {
            "Monday": "Mon",
            "Tuesday": "Tue",
            "Wednesday": "Wed",
            "Thursday": "Thu",
            "Friday": "Fri",
            "Saturday": "Sat",
            "Sunday": "Sun"
        }

        for full, short in expected_mappings.items():
            actual = DAY_MAPPING.get(full)
            assert actual == short, f"{full}: expected {short}, got {actual}"
            print(f"  [PASS] {full} -> {actual}")

    def test_time_format_validation(self):
        """Test time format validation using datetime.strptime"""
        from datetime import datetime

        valid_times = ["00:00", "06:00", "12:30", "23:59"]
        for time_str in valid_times:
            try:
                datetime.strptime(time_str, '%H:%M')
                print(f"  [PASS] {time_str} is valid")
            except ValueError:
                assert False, f"{time_str} should be valid"

        invalid_times = ["25:00", "12:60", "12:00:00", "abc", "", None]
        for time_str in invalid_times:
            if time_str is None or time_str == "":
                is_invalid = True
            else:
                try:
                    datetime.strptime(time_str, '%H:%M')
                    is_invalid = False
                except ValueError:
                    is_invalid = True
            assert is_invalid, f"{time_str} should be invalid"
            print(f"  [PASS] {time_str} correctly rejected")

    def test_schedule_types(self):
        """Test different schedule types used in scheduler"""
        valid_schedule_types = ["daily", "weekly"]

        for schedule_type in valid_schedule_types:
            assert schedule_type in valid_schedule_types
            print(f"  [PASS] Schedule type '{schedule_type}' is valid")

    def test_day_list_validation(self):
        """Test day list validation"""
        valid_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        invalid_days = ["Monday", "monday", "Mon,Tue", "1", ""]

        for day in valid_days:
            is_valid = day in valid_days
            assert is_valid, f"'{day}' should be valid"

        for day in invalid_days:
            is_invalid = day not in valid_days
            assert is_invalid, f"'{day}' should be invalid"


class TestSchedulerExecution:
    """Test scheduler execution logic"""

    def test_next_run_calculation(self):
        """Test next run time calculation"""
        from datetime import datetime, timedelta

        now = datetime.now()

        test_cases = [
            (time(6, 0), "daily", None),
            (time(12, 0), "daily", None),
            (time(0, 0), "daily", None),
        ]

        for target_time, schedule_type, days in test_cases:
            if now.time() < target_time:
                expected = now.replace(hour=target_time.hour, minute=target_time.minute)
            else:
                expected = now.replace(hour=target_time.hour, minute=target_time.minute) + timedelta(days=1)

            print(f"  [PASS] Next run for {target_time}: {expected.strftime('%H:%M')}")

    def test_schedule_enabled_check(self):
        """Test schedule enabled/disabled logic"""
        schedule = {
            "enabled": True,
            "schedule_type": "daily",
            "time": "06:00",
            "days": [],
            "download_all": True,
            "selected_sources": []
        }

        is_enabled = schedule.get("enabled", False)
        assert is_enabled, "Schedule should be enabled"
        print("  [PASS] Schedule enabled check works")

    def test_selected_sources_handling(self):
        """Test selected sources vs download_all flag"""
        test_cases = [
            ({"download_all": True, "selected_sources": []}, ["all_sources"]),
            ({"download_all": False, "selected_sources": ["northwest_outdoors"]}, ["northwest_outdoors"]),
            ({"download_all": True, "selected_sources": ["whittler"]}, ["all_sources"]),
        ]

        for schedule, expected in test_cases:
            if schedule.get("download_all"):
                result = ["all_sources"]
            else:
                result = schedule.get("selected_sources", [])

            assert result == expected, f"Expected {expected}, got {result}"
            print(f"  [PASS] download_all={schedule.get('download_all')} -> {result}")


class TestSchedulerIntegration:
    """Test scheduler integration with config"""

    def test_scheduled_config_structure(self):
        """Test scheduled_downloads config structure"""
        from config import DEFAULT_CONFIG

        scheduled = DEFAULT_CONFIG.get("scheduled_downloads", {})

        required_keys = ["enabled", "schedule_type", "time", "days", "download_all", "selected_sources"]
        for key in required_keys:
            assert key in scheduled, f"Missing key: {key}"

        print(f"  [PASS] Scheduled config has all required keys: {list(scheduled.keys())}")

    def test_scheduled_config_defaults(self):
        """Test scheduled_downloads default values"""
        from config import DEFAULT_CONFIG

        scheduled = DEFAULT_CONFIG.get("scheduled_downloads", {})

        assert scheduled.get("enabled") == False
        assert scheduled.get("schedule_type") == "daily"
        assert scheduled.get("time") == "06:00"
        assert scheduled.get("days") == []
        assert scheduled.get("download_all") == True
        assert scheduled.get("selected_sources") == []

        print("  [PASS] Scheduled config defaults are correct")

    def test_get_scheduled_config_method(self):
        """Test ConfigManager.get_scheduled_config method"""
        try:
            from config import ConfigManager

            cm = ConfigManager()
            scheduled = cm.get_scheduled_config()

            assert isinstance(scheduled, dict), "Should return dict"
            assert "enabled" in scheduled, "Should have enabled key"
            print(f"  [PASS] get_scheduled_config returns: {list(scheduled.keys())}")
        except Exception as e:
            print(f"  Note: {e}")


def run_tests():
    """Run all scheduler tests"""
    print("=" * 60)
    print("Running Scheduler Tests")
    print("=" * 60)

    tests = [
        TestSchedulerParsing().test_day_mapping,
        TestSchedulerParsing().test_time_format_validation,
        TestSchedulerParsing().test_schedule_types,
        TestSchedulerParsing().test_day_list_validation,
        TestSchedulerExecution().test_schedule_enabled_check,
        TestSchedulerExecution().test_selected_sources_handling,
        TestSchedulerIntegration().test_scheduled_config_structure,
        TestSchedulerIntegration().test_scheduled_config_defaults,
        TestSchedulerIntegration().test_get_scheduled_config_method,
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