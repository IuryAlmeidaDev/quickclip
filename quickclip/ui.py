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
        on_upload_youtube: Optional[Callable[[], None]] = None,
        root: Optional[Union[tk.Tk, tk.Toplevel]] = None,
    ):
        self.root = root if root is not None else tk.Tk()
        self.on_toggle_record = on_toggle_record
        self.on_open_folder = on_open_folder
        self.on_upload_youtube = on_upload_youtube or on_open_youtube or (lambda: None)
        self.on_open_youtube = self.on_upload_youtube

        self.root.title("QuickClip")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("325x48+60+60")
        self.root.configure(bg="#f59e0b")

        # Apply Win32 NOACTIVATE style so clicks don't steal game focus
        self.apply_win32_styles()

        # Dragging variables
        self._drag_data = {"x": 0, "y": 0}

        # UI Layout: Deep Obsidian Frame with Gold Accent Border
        self.frame = tk.Frame(self.root, bg="#0d0e15", bd=0)
        self.frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Brand / Game Tag
        self.brand_frame = tk.Frame(self.frame, bg="#0d0e15")
        self.brand_frame.pack(side="left", padx=(8, 2), pady=4)

        self.lbl_brand = tk.Label(
            self.brand_frame,
            text="AION 2",
            bg="#0d0e15",
            fg="#f59e0b",
            font=("Segoe UI", 8, "bold"),
        )
        self.lbl_brand.pack(anchor="w")

        self.lbl_hotkey_hint = tk.Label(
            self.brand_frame,
            text="HOTKEY F10",
            bg="#0d0e15",
            fg="#38bdf8",
            font=("Segoe UI", 6, "bold"),
        )
        self.lbl_hotkey_hint.pack(anchor="w")

        # Record Button
        self.btn_record = tk.Button(
            self.frame,
            text="⚪ REC",
            bg="#2a1215",
            fg="#ef4444",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            activebackground="#450a0a",
            activeforeground="#fca5a5",
            cursor="hand2",
            takefocus=False,
            padx=6,
            pady=2,
            command=self.on_toggle_record,
        )
        self.btn_record.pack(side="left", padx=4, pady=6)

        # Status / Timer Pill
        self.lbl_status = tk.Label(
            self.frame,
            text="00:00",
            bg="#181a24",
            fg="#10b981",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=2,
        )
        self.lbl_status.pack(side="left", padx=3, pady=6)

        # Right Action Buttons
        self.btn_close = tk.Button(
            self.frame,
            text="✕",
            bg="#181a24",
            fg="#64748b",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            takefocus=False,
            padx=4,
            pady=2,
            command=self.root.destroy,
        )
        self.btn_close.pack(side="right", padx=(2, 6))

        self.btn_folder = tk.Button(
            self.frame,
            text="📁",
            bg="#181a24",
            fg="#cbd5e1",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            takefocus=False,
            padx=4,
            pady=2,
            command=self.on_open_folder,
        )
        self.btn_folder.pack(side="right", padx=2)

        self.btn_youtube = tk.Button(
            self.frame,
            text="🚀",
            bg="#181a24",
            fg="#ef4444",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            takefocus=False,
            padx=4,
            pady=2,
            command=self.on_upload_youtube,
        )
        self.btn_youtube.pack(side="right", padx=2)

        # Dragging bindings
        for w in (self.frame, self.brand_frame, self.lbl_brand, self.lbl_hotkey_hint, self.lbl_status):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

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
            self.lbl_status.config(text=time_str, bg="#450a0a", fg="#f87171")
        else:
            self.btn_record.config(text="⚪ REC", bg="#2a1215", fg="#ef4444")
            self.lbl_status.config(text="Pronto", bg="#181a24", fg="#10b981")

    def set_processing_state(self):
        self.btn_record.config(text="⏳", bg="#451a03", fg="#fbbf24")
        self.lbl_status.config(text="Criando...", bg="#2d1a04", fg="#fbbf24")

    def set_ignored_state(self, message: str = "Muito curto"):
        self.btn_record.config(text="⚪ REC", bg="#2a1215", fg="#ef4444")
        self.lbl_status.config(text=message, bg="#450a0a", fg="#f87171")

    def set_uploading_state(self, percent: int = 0):
        self.btn_record.config(text="🚀", bg="#1e1b4b", fg="#818cf8")
        self.lbl_status.config(text=f"Up {percent}%", bg="#1e1b4b", fg="#818cf8")

    def set_uploaded_state(self, message: str = "Postado!"):
        self.btn_record.config(text="✓", bg="#064e3b", fg="#34d399")
        self.lbl_status.config(text=message, bg="#064e3b", fg="#34d399")


    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root - self.root.winfo_x()
        self._drag_data["y"] = event.y_root - self.root.winfo_y()

    def _do_drag(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
