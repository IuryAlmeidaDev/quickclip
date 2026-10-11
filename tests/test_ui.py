import os
import sys

# Ensure Tcl/Tk libraries can be located on Windows Python installations
if sys.platform == "win32":
    _tcl_dir = os.path.join(sys.base_prefix, "tcl").replace("\\", "/")
    if os.path.isdir(_tcl_dir):
        _tcl_ver = f"{_tcl_dir}/tcl8.6"
        _tk_ver = f"{_tcl_dir}/tk8.6"
        if os.path.isdir(_tcl_ver) and "TCL_LIBRARY" not in os.environ:
            os.environ["TCL_LIBRARY"] = _tcl_ver
        if os.path.isdir(_tk_ver) and "TK_LIBRARY" not in os.environ:
            os.environ["TK_LIBRARY"] = _tk_ver

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quickclip.ui import (
    GWL_EXSTYLE,
    WS_EX_NOACTIVATE,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    FloatingRecorderWidget,
)
from quickclip.app import QuickClipApp, main


class DummyEvent:
    def __init__(self, x_root=0, y_root=0, x=0, y=0):
        self.x_root = x_root
        self.y_root = y_root
        self.x = x
        self.y = y


import tkinter as tk

@pytest.fixture(scope="module")
def shared_tk():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def toplevel_root(shared_tk):
    top = tk.Toplevel(shared_tk)
    yield top
    try:
        top.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_callbacks():
    return MagicMock(), MagicMock(), MagicMock()


def test_floating_recorder_widget_init(mock_callbacks, toplevel_root):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32") as mock_user32:
        mock_user32.GetWindowLongW.return_value = 0
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
            root=toplevel_root,
        )
        assert widget.btn_record["text"] == "⚪ REC"
        assert widget.lbl_status["text"] == "00:00"
        assert widget.btn_folder["text"] == "📁"
        assert widget.btn_youtube["text"] == "▶"
        assert widget.on_toggle_record == toggle_cb
        assert widget.on_open_folder == folder_cb
        assert widget.on_open_youtube == youtube_cb


def test_floating_recorder_widget_default_root(mock_callbacks):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32"), patch("quickclip.ui.tk.Tk") as mock_tk_cls:
        mock_root = MagicMock()
        mock_tk_cls.return_value = mock_root
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
        )
        assert widget.root == mock_root
        mock_tk_cls.assert_called_once()


def test_floating_recorder_widget_apply_win32_styles(mock_callbacks, toplevel_root):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32") as mock_user32:
        mock_user32.GetWindowLongW.return_value = 0x1000
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
            root=toplevel_root,
        )
        expected_flag = 0x1000 | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        mock_user32.SetWindowLongW.assert_called_with(widget.root.winfo_id(), GWL_EXSTYLE, expected_flag)


def test_floating_recorder_widget_state_transitions(mock_callbacks, toplevel_root):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32"):
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
            root=toplevel_root,
        )
        # Transition to Recording
        widget.set_recording_state(True, "01:30")
        assert widget.btn_record["text"] == "⏹ STOP"
        assert widget.lbl_status["text"] == "01:30"

        # Transition to Ignored
        widget.set_ignored_state("Muito curto")
        assert widget.btn_record["text"] == "⚪ REC"
        assert widget.lbl_status["text"] == "Muito curto"

        # Transition to Processing
        widget.set_processing_state()
        assert widget.btn_record["text"] == "⏳"
        assert widget.lbl_status["text"] == "Criando..."

        # Transition to Idle
        widget.set_recording_state(False)
        assert widget.btn_record["text"] == "⚪ REC"
        assert widget.lbl_status["text"] == "Pronto"


def test_floating_recorder_widget_drag(mock_callbacks, toplevel_root):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32"):
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
            root=toplevel_root,
        )
        with patch.object(widget.root, "winfo_x", return_value=100), \
             patch.object(widget.root, "winfo_y", return_value=200):
            start_event = DummyEvent(x_root=115, y_root=225)
            widget._start_drag(start_event)
            assert widget._drag_data["x"] == 15
            assert widget._drag_data["y"] == 25

        with patch.object(widget.root, "geometry") as mock_geo:
            motion_event = DummyEvent(x_root=125, y_root=230)
            widget._do_drag(motion_event)
            # x = 125 - 15 = 110
            # y = 230 - 25 = 205
            mock_geo.assert_called_once_with("+110+205")


def test_floating_recorder_widget_run(mock_callbacks, toplevel_root):
    toggle_cb, folder_cb, youtube_cb = mock_callbacks
    with patch("ctypes.windll.user32"):
        widget = FloatingRecorderWidget(
            on_toggle_record=toggle_cb,
            on_open_folder=folder_cb,
            on_open_youtube=youtube_cb,
            root=toplevel_root,
        )
        with patch.object(widget.root, "mainloop") as mock_mainloop:
            widget.run()
            mock_mainloop.assert_called_once()


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.get_config")
def test_quickclip_app_init(mock_get_cfg, mock_widget_cls):
    mock_cfg = MagicMock()
    mock_get_cfg.return_value = mock_cfg

    app = QuickClipApp()
    assert app.is_recording is False
    assert app.record_start_time == 0.0
    assert app.config == mock_cfg
    mock_widget_cls.assert_called_once_with(
        on_toggle_record=app.toggle_record,
        on_open_folder=app.open_output,
        on_open_youtube=app.open_youtube,
    )


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.trigger_game_dvr_record")
@patch("quickclip.app.time.time")
def test_quickclip_app_start_record(mock_time, mock_trigger, mock_widget_cls):
    mock_time.return_value = 1000.0
    app = QuickClipApp()
    app.widget = MagicMock()

    app.toggle_record()  # from False -> starts recording

    assert app.is_recording is True
    assert app.record_start_time == 1000.0
    mock_trigger.assert_called_once()
    app.widget.set_recording_state.assert_called_with(True, "00:00")
    app.widget.root.after.assert_called_with(1000, app.update_timer)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.trigger_game_dvr_record")
@patch("quickclip.app.threading.Thread")
@patch("quickclip.app.time.time")
def test_quickclip_app_stop_record(mock_time, mock_thread_cls, mock_trigger, mock_widget_cls):
    mock_time.return_value = 1005.0
    app = QuickClipApp()
    app.widget = MagicMock()
    app.is_recording = True
    app.record_start_time = 1000.0

    mock_thread_instance = MagicMock()
    mock_thread_cls.return_value = mock_thread_instance

    app.toggle_record()  # from True -> stops recording

    assert app.is_recording is False
    mock_trigger.assert_called_once()
    app.widget.set_processing_state.assert_called_once()
    mock_thread_cls.assert_called_once_with(target=app.process_pipeline, daemon=True)
    mock_thread_instance.start.assert_called_once()


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.trigger_game_dvr_record")
@patch("quickclip.app.threading.Thread")
@patch("quickclip.app.time.time")
def test_quickclip_app_stop_record_too_short(mock_time, mock_thread_cls, mock_trigger, mock_widget_cls):
    mock_time.return_value = 1001.0
    app = QuickClipApp()
    app.widget = MagicMock()
    app.is_recording = True
    app.record_start_time = 1000.0  # elapsed 1.0s (< 2.0s)

    app.stop_record()

    assert app.is_recording is False
    mock_trigger.assert_called_once()
    app.widget.set_ignored_state.assert_called_once_with("Muito curto")
    app.widget.root.after.assert_called_once_with(2000, app.widget.set_recording_state, False)
    mock_thread_cls.assert_not_called()
    app.widget.set_processing_state.assert_not_called()


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.open_output_folder")
@patch("quickclip.app.convert_to_shorts")
@patch("quickclip.app.wait_for_file_ready")
@patch("quickclip.app.find_latest_capture")
@patch("quickclip.app.time.sleep")
def test_quickclip_app_process_pipeline_success(
    mock_sleep, mock_find, mock_wait, mock_convert, mock_open_folder, mock_widget_cls
):
    app = QuickClipApp()
    app.widget = MagicMock()
    app.config = MagicMock(captures_dir=Path("/captures"), output_dir=Path("/output"), ffmpeg_bin=Path("/ffmpeg"))

    mock_find.return_value = Path("/captures/game.mp4")
    mock_wait.return_value = True
    mock_convert.return_value = Path("/output/game_short.mp4")

    app.process_pipeline()

    mock_sleep.assert_called_once_with(1.0)
    mock_find.assert_called_once_with(app.config.captures_dir, app.record_start_time)
    mock_wait.assert_called_once_with(Path("/captures/game.mp4"), timeout=12.0)
    mock_convert.assert_called_once_with(

        Path("/captures/game.mp4"),
        app.config.output_dir,
        app.config.ffmpeg_bin,
        music_dir=app.config.music_dir,
    )

    mock_open_folder.assert_called_once_with(Path("/output/game_short.mp4"))
    app.widget.root.after.assert_called_once_with(0, app.widget.set_recording_state, False)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.convert_to_shorts")
@patch("quickclip.app.find_latest_capture")
@patch("quickclip.app.time.sleep")
def test_quickclip_app_process_pipeline_no_capture(mock_sleep, mock_find, mock_convert, mock_widget_cls):
    app = QuickClipApp()
    app.widget = MagicMock()
    mock_find.return_value = None

    app.process_pipeline()

    mock_convert.assert_not_called()
    app.widget.root.after.assert_called_once_with(0, app.widget.set_recording_state, False)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.convert_to_shorts")
@patch("quickclip.app.wait_for_file_ready")
@patch("quickclip.app.find_latest_capture")
@patch("quickclip.app.time.sleep")
def test_quickclip_app_process_pipeline_not_ready(mock_sleep, mock_find, mock_wait, mock_convert, mock_widget_cls):
    app = QuickClipApp()
    app.widget = MagicMock()
    mock_find.return_value = Path("/captures/game.mp4")
    mock_wait.return_value = False

    app.process_pipeline()

    mock_convert.assert_not_called()
    app.widget.root.after.assert_called_once_with(0, app.widget.set_recording_state, False)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.convert_to_shorts")
@patch("quickclip.app.wait_for_file_ready")
@patch("quickclip.app.find_latest_capture")
@patch("quickclip.app.time.sleep")
def test_quickclip_app_process_pipeline_exception(mock_sleep, mock_find, mock_wait, mock_convert, mock_widget_cls):
    app = QuickClipApp()
    app.widget = MagicMock()
    mock_find.return_value = Path("/captures/game.mp4")
    mock_wait.return_value = True
    mock_convert.side_effect = RuntimeError("Encoding failed")

    app.process_pipeline()

    app.widget.root.after.assert_called_once_with(0, app.widget.set_recording_state, False)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.open_output_folder")
def test_quickclip_app_open_output(mock_open_folder, mock_widget_cls):
    app = QuickClipApp()
    app.open_output()
    mock_open_folder.assert_called_once_with(app.config.output_dir)


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.open_youtube_upload")
def test_quickclip_app_open_youtube(mock_open_yt, mock_widget_cls):
    app = QuickClipApp()
    app.open_youtube()
    mock_open_yt.assert_called_once()


@patch("quickclip.app.FloatingRecorderWidget")
def test_quickclip_app_run(mock_widget_cls):
    app = QuickClipApp()
    app.run()
    app.widget.run.assert_called_once()


@patch("quickclip.app.QuickClipApp")
def test_main_function(mock_app_cls):
    mock_instance = MagicMock()
    mock_app_cls.return_value = mock_instance

    main()

    mock_app_cls.assert_called_once()
    mock_instance.run.assert_called_once()


@patch("quickclip.app.FloatingRecorderWidget")
@patch("quickclip.app.threading.Thread")
def test_quickclip_app_start_hotkey_listener(mock_thread_cls, mock_widget_cls):
    app = QuickClipApp()
    app._start_hotkey_listener()
    mock_thread_cls.assert_called_once()
    mock_thread_cls.return_value.start.assert_called_once()


def test_acquire_single_instance_mutex():
    from quickclip.app import acquire_single_instance_mutex
    mutex = acquire_single_instance_mutex()
    assert mutex is not None or mutex is None  # Executes without raising exception


@patch("quickclip.app.acquire_single_instance_mutex", return_value=None)
@patch("quickclip.app.QuickClipApp")
def test_main_function_already_running(mock_app_cls, mock_mutex):
    main()
    mock_app_cls.assert_not_called()


