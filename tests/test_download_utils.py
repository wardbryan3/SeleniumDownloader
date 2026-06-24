"""
Test download utilities, especially the FFmpeg promo tag overlay
"""
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOverlayPromoWithTag:
    """Test the overlay_promo_with_tag method"""

    def test_missing_promo_file(self):
        """Should return False if promo file doesn't exist"""
        from download_utils import DownloadUtilities
        result = DownloadUtilities.overlay_promo_with_tag(
            "/nonexistent/promo.mp3", "/nonexistent/tag.wav", "/tmp/output.mp3"
        )
        assert result is False
        print("  ✓ Missing promo file returns False")

    def test_missing_tag_file(self):
        """Should return False if tag file doesn't exist"""
        from download_utils import DownloadUtilities

        # Create a fake promo file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as promo:
            promo.write(b'fake audio data')
            promo_path = promo.name

        try:
            result = DownloadUtilities.overlay_promo_with_tag(
                promo_path, "/nonexistent/tag.wav", "/tmp/output.mp3"
            )
            assert result is False
            print("  ✓ Missing tag file returns False")
        finally:
            os.unlink(promo_path)

    def test_successful_overlay(self):
        """Should return True when FFmpeg succeeds"""
        from download_utils import DownloadUtilities

        # Create fake input files
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as promo:
            promo.write(b'fake audio')
            promo_path = promo.name

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tag:
            tag.write(b'fake tag audio')
            tag_path = tag.name

        output_path = tempfile.mktemp(suffix='.mp3')

        try:
            # Mock _get_audio_duration to return 30 seconds
            with patch.object(DownloadUtilities, '_get_audio_duration', return_value=30.0):
                # Mock subprocess.run to simulate FFmpeg success and create output file
                def mock_run(cmd, **kwargs):
                    mock_result = MagicMock()
                    if 'ffprobe' in cmd[0]:
                        mock_result.returncode = 0
                        mock_result.stdout = '30.0'
                    else:  # ffmpeg
                        mock_result.returncode = 0
                        mock_result.stderr = ''
                        # Create the output file to simulate success
                        Path(output_path).write_bytes(b'fake output')
                    return mock_result

                with patch('download_utils.subprocess.run', side_effect=mock_run):
                    result = DownloadUtilities.overlay_promo_with_tag(
                        promo_path, tag_path, output_path, overlap_seconds=10
                    )

            assert result is True
            print("  ✓ Successful overlay returns True")
        finally:
            if os.path.exists(promo_path):
                os.unlink(promo_path)
            if os.path.exists(tag_path):
                os.unlink(tag_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_ffmpeg_failure(self):
        """Should return False when FFmpeg fails"""
        from download_utils import DownloadUtilities

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as promo:
            promo.write(b'fake audio')
            promo_path = promo.name

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tag:
            tag.write(b'fake tag audio')
            tag_path = tag.name

        output_path = tempfile.mktemp(suffix='.mp3')

        try:
            with patch.object(DownloadUtilities, '_get_audio_duration', return_value=30.0):
                def mock_run(cmd, **kwargs):
                    mock_result = MagicMock()
                    mock_result.returncode = 1
                    mock_result.stderr = 'Some error'
                    return mock_result

                with patch('download_utils.subprocess.run', side_effect=mock_run):
                    result = DownloadUtilities.overlay_promo_with_tag(
                        promo_path, tag_path, output_path, overlap_seconds=10
                    )

            assert result is False
            print("  ✓ FFmpeg failure returns False")
        finally:
            if os.path.exists(promo_path):
                os.unlink(promo_path)
            if os.path.exists(tag_path):
                os.unlink(tag_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_promo_too_short(self):
        """Should return False if promo is shorter than overlap"""
        from download_utils import DownloadUtilities

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as promo:
            promo.write(b'fake audio')
            promo_path = promo.name

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tag:
            tag.write(b'fake tag audio')
            tag_path = tag.name

        try:
            # Promo is 5 seconds but overlap is 10
            with patch.object(DownloadUtilities, '_get_audio_duration', return_value=5.0):
                result = DownloadUtilities.overlay_promo_with_tag(
                    promo_path, tag_path, "/tmp/output.mp3", overlap_seconds=10
                )

            assert result is False
            print("  ✓ Short promo returns False")
        finally:
            if os.path.exists(promo_path):
                os.unlink(promo_path)
            if os.path.exists(tag_path):
                os.unlink(tag_path)


def run_tests():
    """Run all download utils tests"""
    print("=" * 60)
    print("Running Download Utils Tests")
    print("=" * 60)

    tester = TestOverlayPromoWithTag()

    tests = [
        tester.test_missing_promo_file,
        tester.test_missing_tag_file,
        tester.test_successful_overlay,
        tester.test_ffmpeg_failure,
        tester.test_promo_too_short,
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
