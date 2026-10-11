import ctypes
import time
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Virtual Key Codes
VK_LWIN = 0x5B
VK_MENU = 0x12  # Alt
VK_R = 0x52
KEYEVENTF_KEYUP = 0x0002


def trigger_game_dvr_record() -> None:
    """Simulates Win + Alt + R key combination to toggle Windows GameDVR recording."""
    user32 = ctypes.windll.user32
    # Press Win + Alt + R
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_R, 0, 0, 0)
    time.sleep(0.05)
    # Release R + Alt + Win
    user32.keybd_event(VK_R, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    logger.info("Sent Win+Alt+R to toggle GameDVR")


def find_latest_capture(captures_dir: Path, after_time: float) -> Optional[Path]:
    """Finds the most recently created .mp4 file in captures_dir created after after_time."""
    if not captures_dir.exists():
        return None

    mp4_files = list(captures_dir.glob("*.mp4"))
    candidates = [f for f in mp4_files if f.stat().st_mtime >= after_time - 1.0]
    if not candidates:
        return None

    candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return candidates[0]


def wait_for_file_ready(
    file_path: Path, timeout: float = 10.0, poll_interval: float = 0.5
) -> bool:
    """Waits until the file is no longer locked by Windows/GameDVR write stream."""
    start = time.time()
    last_size = -1
    while time.time() - start < timeout:
        try:
            if file_path.exists():
                curr_size = file_path.stat().st_size
                with open(file_path, "ab"):
                    pass
                if curr_size > 0 and curr_size == last_size:
                    return True
                last_size = curr_size
        except (PermissionError, OSError):
            pass
        time.sleep(poll_interval)
    return False
