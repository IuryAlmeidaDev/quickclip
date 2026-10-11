import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from quickclip.capture import (
    trigger_game_dvr_record,
    find_latest_capture,
    wait_for_file_ready,
    VK_LWIN,
    VK_MENU,
    VK_R,
    KEYEVENTF_KEYUP,
)


def test_find_latest_capture_success(tmp_path: Path):
    start_time = time.time()
    time.sleep(0.01)
    test_video = tmp_path / "clip.mp4"
    test_video.write_bytes(b"dummy video data")

    latest = find_latest_capture(tmp_path, after_time=start_time)
    assert latest == test_video


def test_find_latest_capture_no_files(tmp_path: Path):
    start_time = time.time()
    # No files in tmp_path
    assert find_latest_capture(tmp_path, after_time=start_time) is None

    # Only older files
    older_video = tmp_path / "older.mp4"
    older_video.write_bytes(b"old")
    # Set older mtime to 10 seconds before start_time
    import os
    os.utime(older_video, (start_time - 10, start_time - 10))
    assert find_latest_capture(tmp_path, after_time=start_time) is None


def test_find_latest_capture_dir_not_exists(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist"
    assert find_latest_capture(non_existent, after_time=time.time()) is None


def test_find_latest_capture_picks_newest(tmp_path: Path):
    start_time = time.time()
    v1 = tmp_path / "v1.mp4"
    v2 = tmp_path / "v2.mp4"
    v1.write_bytes(b"video 1")
    v2.write_bytes(b"video 2")

    import os
    os.utime(v1, (start_time + 1, start_time + 1))
    os.utime(v2, (start_time + 5, start_time + 5))

    latest = find_latest_capture(tmp_path, after_time=start_time)
    assert latest == v2


def test_find_latest_capture_ignores_non_mp4(tmp_path: Path):
    start_time = time.time()
    txt_file = tmp_path / "clip.txt"
    txt_file.write_bytes(b"text file")

    assert find_latest_capture(tmp_path, after_time=start_time) is None


def test_wait_for_file_ready_success(tmp_path: Path):
    test_file = tmp_path / "ready.mp4"
    test_file.write_bytes(b"test data")
    assert wait_for_file_ready(test_file, timeout=1.0) is True


def test_wait_for_file_ready_timeout_non_existent(tmp_path: Path):
    test_file = tmp_path / "missing.mp4"
    assert wait_for_file_ready(test_file, timeout=0.1) is False


def test_wait_for_file_ready_timeout_zero_size(tmp_path: Path):
    test_file = tmp_path / "empty.mp4"
    test_file.touch()
    assert wait_for_file_ready(test_file, timeout=0.1) is False


def test_trigger_game_dvr_record():
    with patch("ctypes.windll.user32.keybd_event") as mock_keybd_event:
        trigger_game_dvr_record()

        expected_calls = [
            # Press Win + Alt + R
            (VK_LWIN, 0, 0, 0),
            (VK_MENU, 0, 0, 0),
            (VK_R, 0, 0, 0),
            # Release R + Alt + Win
            (VK_R, 0, KEYEVENTF_KEYUP, 0),
            (VK_MENU, 0, KEYEVENTF_KEYUP, 0),
            (VK_LWIN, 0, KEYEVENTF_KEYUP, 0),
        ]

        actual_calls = [call.args for call in mock_keybd_event.call_args_list]
        assert actual_calls == expected_calls
