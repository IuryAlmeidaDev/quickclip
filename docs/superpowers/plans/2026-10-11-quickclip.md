# QuickClip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight, floating screen recorder and automated YouTube Shorts converter for gaming clips with zero gameplay interruption.

**Architecture:** A Python Win32 floating widget (`WS_EX_TOPMOST | WS_EX_NOACTIVATE`) that triggers Windows GameDVR hardware-accelerated recording (`Win + Alt + R`) without stealing window focus from the game, monitors `Videos/Captures`, runs FFmpeg to convert the clip into 9:16 vertical Shorts (blurred background + centered gameplay), and provides direct output/upload handling.

**Tech Stack:** Python 3.12, tkinter, ctypes (Win32 API), imageio-ffmpeg, pytest.

**Spec:** `docs/superpowers/specs/2026-10-11-quickclip-design.md`

## Global Constraints
- Platform: Windows 10 / 11
- Python: 3.12+
- FFmpeg: Use `imageio_ffmpeg.get_ffmpeg_exe()`
- Widget focus: Must set `WS_EX_NOACTIVATE` so clicking the record button does not switch active focus away from the game
- Output format: MP4 (H.264/AAC), 1080x1920 (9:16 vertical), maintaining audio sync

---

### Task 1: Configuration & Environment Setup

**Files:**
- Create: `quickclip/__init__.py`
- Create: `quickclip/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass and `get_config()` returning paths: `captures_dir`, `output_dir`, `ffmpeg_bin`.

- [ ] **Step 1: Write failing test for config module**

```python
# tests/test_config.py
from pathlib import Path
from quickclip.config import get_config, Config

def test_config_paths():
    cfg = get_config()
    assert isinstance(cfg, Config)
    assert Path(cfg.captures_dir).exists()
    assert Path(cfg.ffmpeg_bin).exists()
    assert Path(cfg.output_dir).name == "shorts"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`  
Expected: FAIL with ModuleNotFoundError: No module named 'quickclip'

- [ ] **Step 3: Implement config module**

```python
# quickclip/__init__.py
"""QuickClip - Automated Gaming Highlight Recorder and Shorts Converter."""
__version__ = "0.1.0"
```

```python
# quickclip/config.py
from dataclasses import dataclass
from pathlib import Path
import imageio_ffmpeg

@dataclass(frozen=True)
class Config:
    captures_dir: Path
    output_dir: Path
    ffmpeg_bin: Path

def get_config() -> Config:
    user_home = Path.home()
    captures_dir = user_home / "Videos" / "Captures"
    if not captures_dir.exists():
        captures_dir.mkdir(parents=True, exist_ok=True)

    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "output" / "shorts"
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = Path(imageio_ffmpeg.get_ffmpeg_exe())
    return Config(
        captures_dir=captures_dir,
        output_dir=output_dir,
        ffmpeg_bin=ffmpeg_bin,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add quickclip/__init__.py quickclip/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add config and environment paths"
```

---

### Task 2: Video Processor (FFmpeg Shorts Converter)

**Files:**
- Create: `quickclip/processor.py`
- Create: `tests/test_processor.py`

**Interfaces:**
- Consumes: `Config` from `quickclip.config`
- Produces: `build_ffmpeg_filter() -> str`, `convert_to_shorts(input_path: Path, output_dir: Path, ffmpeg_bin: Path) -> Path`

- [ ] **Step 1: Write failing test for filter generation and conversion command**

```python
# tests/test_processor.py
from pathlib import Path
from quickclip.processor import build_ffmpeg_filter, generate_output_filename

def test_build_ffmpeg_filter():
    filter_chain = build_ffmpeg_filter(target_width=1080, target_height=1920)
    assert "split" in filter_chain
    assert "boxblur" in filter_chain or "gblur" in filter_chain
    assert "overlay" in filter_chain
    assert "1080" in filter_chain
    assert "1920" in filter_chain

def test_generate_output_filename():
    name = generate_output_filename("Aion_2026.mp4")
    assert name.endswith(".mp4")
    assert "short" in name
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_processor.py -v`  
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Implement video processor**

```python
# quickclip/processor.py
from pathlib import Path
from datetime import datetime
import subprocess
import logging

logger = logging.getLogger(__name__)

def build_ffmpeg_filter(target_width: int = 1080, target_height: int = 1920) -> str:
    """Build FFmpeg complex filter chain for 9:16 Shorts with blurred background."""
    # Split input into background and foreground:
    # 1. Background: scale to crop filling 1080x1920, apply boxblur and slight darken
    # 2. Foreground: scale to fit 1080 width preserving aspect ratio
    # 3. Overlay foreground centered on background
    return (
        f"[0:v]split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},boxblur=20:5,colorchannelmixer=aa=1:rr=0.7:gg=0.7:bb=0.7[bg];"
        f"[fg_raw]scale={target_width}:-1[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
    )

def generate_output_filename(source_filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_stem = Path(source_filename).stem.replace(" ", "_")
    return f"{clean_stem}_{timestamp}_short.mp4"

def convert_to_shorts(input_path: Path, output_dir: Path, ffmpeg_bin: Path) -> Path:
    """Converts an input video into a 1080x1920 9:16 Short."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = generate_output_filename(input_path.name)
    output_path = output_dir / out_name

    filter_complex = build_ffmpeg_filter(1080, 1920)

    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path),
    ]

    logger.info("Executing FFmpeg conversion: %s", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg error: %s", result.stderr)
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}: {result.stderr[-500:]}")

    return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_processor.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add quickclip/processor.py tests/test_processor.py
git commit -m "feat: implement FFmpeg Shorts video processor"
```

---

### Task 3: GameDVR Capture Engine

**Files:**
- Create: `quickclip/capture.py`
- Create: `tests/test_capture.py`

**Interfaces:**
- Consumes: `Config`
- Produces: `trigger_game_dvr_record()`, `find_latest_capture(captures_dir: Path, after_time: float) -> Optional[Path]`, `wait_for_file_ready(file_path: Path, timeout: float = 10.0) -> bool`

- [ ] **Step 1: Write failing test for capture file detection**

```python
# tests/test_capture.py
import time
from pathlib import Path
from quickclip.capture import find_latest_capture, wait_for_file_ready

def test_find_latest_capture(tmp_path):
    start_time = time.time()
    time.sleep(0.01)
    test_video = tmp_path / "clip.mp4"
    test_video.write_bytes(b"dummy video data")

    latest = find_latest_capture(tmp_path, after_time=start_time)
    assert latest == test_video

def test_wait_for_file_ready(tmp_path):
    test_file = tmp_path / "ready.mp4"
    test_file.write_bytes(b"test data")
    assert wait_for_file_ready(test_file, timeout=1.0) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_capture.py -v`  
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Implement capture engine**

```python
# quickclip/capture.py
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

def wait_for_file_ready(file_path: Path, timeout: float = 10.0) -> bool:
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
        time.sleep(0.5)
    return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_capture.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add quickclip/capture.py tests/test_capture.py
git commit -m "feat: implement GameDVR capture trigger and file watcher"
```

---

### Task 4: Publisher / Output Manager

**Files:**
- Create: `quickclip/publisher.py`
- Create: `tests/test_publisher.py`

**Interfaces:**
- Produces: `open_output_folder(path: Path)`, `prepare_shorts_metadata(video_name: str) -> dict`, `open_youtube_upload()`

- [ ] **Step 1: Write failing test for metadata generation**

```python
# tests/test_publisher.py
from quickclip.publisher import prepare_shorts_metadata

def test_prepare_shorts_metadata():
    meta = prepare_shorts_metadata("Aion_Boss_Fight.mp4")
    assert "title" in meta
    assert "#Shorts" in meta["tags"]
    assert "#Aion" in meta["tags"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_publisher.py -v`  
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Implement publisher module**

```python
# quickclip/publisher.py
import webbrowser
import subprocess
from pathlib import Path
from typing import Dict, Any

def prepare_shorts_metadata(video_name: str) -> Dict[str, Any]:
    return {
        "title": f"Aion Gameplay Highlight #Shorts",
        "description": "Momentos insanos de Aion! #Aion #MMORPG #Shorts #Gaming",
        "tags": ["#Shorts", "#Aion", "#MMORPG", "#Gaming"],
    }

def open_output_folder(path: Path) -> None:
    folder = path if path.is_dir() else path.parent
    subprocess.Popen(f'explorer /select,"{path}"' if path.is_file() else f'explorer "{folder}"')

def open_youtube_upload() -> None:
    webbrowser.open("https://studio.youtube.com/channel/UC/videos/upload?d=ud")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_publisher.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add quickclip/publisher.py tests/test_publisher.py
git commit -m "feat: implement publisher and metadata utilities"
```

---

### Task 5: Floating GUI Widget & App Assembly

**Files:**
- Create: `quickclip/ui.py`
- Create: `quickclip/app.py`
- Create: `run.bat`

**Interfaces:**
- Produces: `FloatingRecorderWidget` in `quickclip.ui`, `main()` entrypoint in `quickclip.app`, and `run.bat` one-click launcher.

- [ ] **Step 1: Implement the Win32 Non-Activating Floating Widget**

```python
# quickclip/ui.py
import tkinter as tk
import ctypes
from typing import Callable

# Win32 Constants
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

class FloatingRecorderWidget:
    def __init__(self, on_toggle_record: Callable[[], None], on_open_folder: Callable[[], None]):
        self.root = tk.Tk()
        self.on_toggle_record = on_toggle_record
        self.on_open_folder = on_open_folder

        self.root.title("QuickClip")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("180x42+50+50")
        self.root.configure(bg="#121214")

        # Apply Win32 NOACTIVATE style so clicks don't steal game focus
        self.apply_win32_styles()

        # Dragging variables
        self._drag_data = {"x": 0, "y": 0}

        # UI Layout
        self.frame = tk.Frame(self.root, bg="#18181b", bd=1, relief="ridge")
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.btn_record = tk.Button(
            self.frame,
            text="⚪ REC",
            bg="#27272a",
            fg="#ef4444",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            activebackground="#3f3f46",
            activeforeground="#f87171",
            cursor="hand2",
            command=self.on_toggle_record,
        )
        self.btn_record.pack(side="left", padx=5, pady=4)

        self.lbl_status = tk.Label(
            self.frame,
            text="00:00",
            bg="#18181b",
            fg="#a1a1aa",
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_status.pack(side="left", padx=4)

        self.btn_folder = tk.Button(
            self.frame,
            text="📁",
            bg="#18181b",
            fg="#71717a",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            command=self.on_open_folder,
        )
        self.btn_folder.pack(side="right", padx=4)

        # Dragging bindings
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._do_drag)
        self.lbl_status.bind("<Button-1>", self._start_drag)
        self.lbl_status.bind("<B1-Motion>", self._do_drag)

    def apply_win32_styles(self):
        hwnd = self.root.winfo_id()
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)

    def set_recording_state(self, is_recording: bool, time_str: str = "00:00"):
        if is_recording:
            self.btn_record.config(text="⏹ STOP", bg="#7f1d1d", fg="#fca5a5")
            self.lbl_status.config(text=time_str, fg="#f87171")
        else:
            self.btn_record.config(text="⚪ REC", bg="#27272a", fg="#ef4444")
            self.lbl_status.config(text="Pronto", fg="#a1a1aa")

    def set_processing_state(self):
        self.btn_record.config(text="⏳", bg="#27272a", fg="#fbbf24")
        self.lbl_status.config(text="Criando...", fg="#fbbf24")

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
```

- [ ] **Step 2: Implement Main Controller Application**

```python
# quickclip/app.py
import time
import threading
from quickclip.config import get_config
from quickclip.capture import trigger_game_dvr_record, find_latest_capture, wait_for_file_ready
from quickclip.processor import convert_to_shorts
from quickclip.publisher import open_output_folder, open_youtube_upload
from quickclip.ui import FloatingRecorderWidget

class QuickClipApp:
    def __init__(self):
        self.config = get_config()
        self.is_recording = False
        self.record_start_time = 0.0
        self.widget = FloatingRecorderWidget(
            on_toggle_record=self.toggle_record,
            on_open_folder=self.open_output,
        )

    def toggle_record(self):
        if not self.is_recording:
            self.start_record()
        else:
            self.stop_record()

    def start_record(self):
        self.is_recording = True
        self.record_start_time = time.time()
        trigger_game_dvr_record()
        self.update_timer()

    def update_timer(self):
        if self.is_recording:
            elapsed = int(time.time() - self.record_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.widget.set_recording_state(True, f"{mins:02d}:{secs:02d}")
            self.widget.root.after(1000, self.update_timer)

    def stop_record(self):
        self.is_recording = False
        trigger_game_dvr_record()
        self.widget.set_processing_state()
        threading.Thread(target=self.process_pipeline, daemon=True).start()

    def process_pipeline(self):
        time.sleep(1.0)
        latest = find_latest_capture(self.config.captures_dir, self.record_start_time)
        if not latest:
            self.widget.set_recording_state(False)
            return

        ready = wait_for_file_ready(latest, timeout=12.0)
        if ready:
            try:
                short_path = convert_to_shorts(latest, self.config.output_dir, self.config.ffmpeg_bin)
                open_output_folder(short_path)
            except Exception as e:
                print(f"Erro ao processar: {e}")
        self.widget.set_recording_state(False)

    def open_output(self):
        open_output_folder(self.config.output_dir)

    def run(self):
        self.widget.run()

if __name__ == "__main__":
    app = QuickClipApp()
    app.run()
```

- [ ] **Step 3: Create One-Click Launcher Batch File**

```bat
@echo off
title QuickClip
python -m quickclip.app
```

- [ ] **Step 4: Commit UI and App**

```bash
git add quickclip/ui.py quickclip/app.py run.bat
git commit -m "feat: implement floating widget and main pipeline launcher"
```

---

### Task 6: End-to-End Verification

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests/ -v`  
Expected: All tests PASS.

- [ ] **Step 2: Commit verified state**

```bash
git commit --allow-empty -m "test: verify all unit tests pass"
```
