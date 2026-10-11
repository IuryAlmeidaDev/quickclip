import ctypes
import threading
import time
from pathlib import Path
from quickclip.capture import find_latest_capture, trigger_game_dvr_record, wait_for_file_ready
from quickclip.config import get_config
from quickclip.processor import convert_to_shorts
from quickclip.publisher import open_output_folder, open_youtube_upload
from quickclip.ui import FloatingRecorderWidget


class QuickClipApp:
    def __init__(self):
        self.config = get_config()
        self.is_recording = False
        self.record_start_time = 0.0
        self.processed_captures: set[str] = set()
        self._init_existing_captures()

        self.widget = FloatingRecorderWidget(
            on_toggle_record=self.toggle_record,
            on_open_folder=self.open_output,
            on_open_youtube=self.open_youtube,
        )

    def _init_existing_captures(self):
        try:
            if self.config.captures_dir.exists():
                for f in self.config.captures_dir.glob("*.mp4"):
                    self.processed_captures.add(f.name)
        except Exception:
            pass

    def _watch_captures(self):
        """Background watcher: converts ANY newly created GameDVR video automatically."""
        while True:
            time.sleep(1.5)
            try:
                if not self.config.captures_dir.exists():
                    continue
                for f in self.config.captures_dir.glob("*.mp4"):
                    if f.name not in self.processed_captures:
                        ready = wait_for_file_ready(f, timeout=15.0)
                        if ready:
                            self.processed_captures.add(f.name)
                            self._process_single_capture(f)
            except Exception:
                pass

    def _process_single_capture(self, capture_path: Path):
        self.widget.root.after(0, self.widget.set_processing_state)
        try:
            short_path = convert_to_shorts(
                capture_path,
                self.config.output_dir,
                self.config.ffmpeg_bin,
                music_dir=self.config.music_dir,
            )
            open_output_folder(short_path)
            self.widget.root.after(0, self.widget.set_recording_state, False)
        except Exception as e:
            print(f"Error processing capture: {e}")
            self.widget.root.after(0, self.widget.set_ignored_state, "Erro FFmpeg")
            self.widget.root.after(2500, self.widget.set_recording_state, False)

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
        if (time.time() - self.record_start_time) < 2.0:
            self.widget.set_ignored_state("Muito curto")
            self.widget.root.after(2000, self.widget.set_recording_state, False)
            return
        self.widget.set_processing_state()
        threading.Thread(target=self.process_pipeline, daemon=True).start()

    def process_pipeline(self):
        time.sleep(1.0)
        latest = find_latest_capture(self.config.captures_dir, self.record_start_time)
        if not latest:
            # Retry up to 8 times waiting for Windows GameDVR to flush the file to disk
            for _ in range(8):
                time.sleep(1.0)
                latest = find_latest_capture(self.config.captures_dir, self.record_start_time)
                if latest:
                    break

        if not latest:
            self.widget.root.after(0, self.widget.set_recording_state, False)
            return

        ready = wait_for_file_ready(latest, timeout=12.0)
        if ready:
            self.processed_captures.add(latest.name)
            try:
                short_path = convert_to_shorts(
                    latest,
                    self.config.output_dir,
                    self.config.ffmpeg_bin,
                    music_dir=self.config.music_dir,
                )
                open_output_folder(short_path)
            except Exception as e:
                print(f"Error processing capture: {e}")
        self.widget.root.after(0, self.widget.set_recording_state, False)

    def open_output(self):
        open_output_folder(self.config.output_dir)

    def open_youtube(self):
        open_youtube_upload()

    def _start_hotkey_listener(self):
        """Spawns a background listener for the F10 global hotkey."""
        def listener():
            user32 = ctypes.windll.user32
            VK_F10 = 0x79
            was_pressed = False
            while True:
                time.sleep(0.05)
                try:
                    is_pressed = bool(user32.GetAsyncKeyState(VK_F10) & 0x8000)
                    if is_pressed and not was_pressed:
                        self.widget.root.after(0, self.toggle_record)
                    was_pressed = is_pressed
                except Exception:
                    pass

        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def run(self):
        threading.Thread(target=self._watch_captures, daemon=True).start()
        self._start_hotkey_listener()
        self.widget.run()


def acquire_single_instance_mutex():
    """Ensures only a single instance of QuickClip runs across the entire system."""
    if not hasattr(ctypes, "windll"):
        return 1
    try:
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\QuickClip_SingleInstance_App_Mutex"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            return None
        return mutex
    except Exception:
        return 1


def main():
    mutex = acquire_single_instance_mutex()
    if mutex is None:
        print("QuickClip is already running.")
        return
    app = QuickClipApp()
    app._single_instance_mutex = mutex
    app.run()


if __name__ == "__main__":
    main()

