import os
import sys
import ctypes

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

import tkinter as tk
from typing import Callable, Optional, Union

# Win32 Constants
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000


class FloatingRecorderWidget:
    def __init__(
        self,
        on_toggle_record: Callable[[], None],
        on_open_folder: Callable[[], None],
        on_open_youtube: Optional[Callable[[], None]] = None,
        root: Optional[Union[tk.Tk, tk.Toplevel]] = None,
    ):
        self.root = root if root is not None else tk.Tk()
        self.on_toggle_record = on_toggle_record
        self.on_open_folder = on_open_folder
        self.on_open_youtube = on_open_youtube if on_open_youtube is not None else (lambda: None)

        self.root.title("QuickClip")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("200x42+50+50")
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
            takefocus=False,
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
            takefocus=False,
            command=self.on_open_folder,
        )
        self.btn_folder.pack(side="right", padx=4)

        self.btn_youtube = tk.Button(
            self.frame,
            text="▶",
            bg="#18181b",
            fg="#ef4444",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            takefocus=False,
            command=self.on_open_youtube,
        )
        self.btn_youtube.pack(side="right", padx=2)

        # Dragging bindings
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._do_drag)
        self.lbl_status.bind("<Button-1>", self._start_drag)
        self.lbl_status.bind("<B1-Motion>", self._do_drag)

    def apply_win32_styles(self):
        self.root.update_idletasks()
        child_hwnd = self.root.winfo_id()
        user32 = ctypes.windll.user32
        try:
            parent_hwnd = user32.GetParent(child_hwnd)
        except Exception:
            parent_hwnd = 0

        targets = [parent_hwnd, child_hwnd] if parent_hwnd else [child_hwnd]

        for h in targets:
            try:
                style = user32.GetWindowLongW(h, GWL_EXSTYLE)
                user32.SetWindowLongW(
                    h, GWL_EXSTYLE, style | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                )
            except Exception:
                pass

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

    def set_ignored_state(self, message: str = "Muito curto"):
        self.btn_record.config(text="⚪ REC", bg="#27272a", fg="#ef4444")
        self.lbl_status.config(text=message, fg="#f87171")

    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root - self.root.winfo_x()
        self._drag_data["y"] = event.y_root - self.root.winfo_y()

    def _do_drag(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
