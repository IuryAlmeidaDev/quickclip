import threading
import time
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


def main():
    app = QuickClipApp()
    app.run()


if __name__ == "__main__":
    main()
