# QuickClip 🎬

**QuickClip** is a lightweight, zero-distraction desktop tool designed for gamers to instantly record gameplay highlights (optimized for *Aion* and other PC games) and automatically produce vertical YouTube Shorts (1080x1920, 9:16) with blurred backgrounds in one seamless click.

---

## Key Features

- **One-Click Recording**: Start and stop recordings directly from an unobtrusive, always-on-top floating HUD.
- **No Focus Stealing (`WS_EX_NOACTIVATE`)**: The widget utilizes native Windows API styles so clicking the HUD buttons never steals keyboard or mouse focus from *Aion*, preventing game window minimization or input interruptions.
- **Automated YouTube Shorts Pipeline**:
  - Automatically captures game clips via Windows GameDVR (`Win+Alt+R`).
  - Converts horizontal 16:9 gameplay footage into high-definition vertical 9:16 Shorts (1080x1920).
  - Creates a dynamic blurred background (boxblur) behind centered, crystal-clear 1080p game footage.
- **Instant Output & Explorer Integration**:
  - Output clips are automatically saved to `output/shorts/` with clean timestamps (`short_YYYYMMDD_HHMMSS.mp4`).
  - Automatically opens Windows Explorer highlighting newly rendered videos.
  - Dedicated folder button (`📁`) on the widget to open the shorts directory at any time.

---

## Requirements

1. **Windows 10 / 11** with **Xbox Game Bar / GameDVR** enabled (default shortcut: `Win + Alt + R`).
2. **Python 3.10+** (Python 3.12 recommended).
3. **FFmpeg** installed and accessible via system `PATH` (or placed in the project directory).

---

## Getting Started

### 1. Launching QuickClip

You can launch QuickClip in either of two ways:

- **Option A (Recommended)**: Double-click `run.bat` in the project root.
- **Option B (Terminal)**:
  ```bash
  python -m quickclip.app
  ```

Once launched, a compact, dark-mode floating HUD appears in the corner of your screen:

```
+------------------------------------+
|  ⚪ REC    00:00               📁  |
+------------------------------------+
```

- **Drag to Move**: Click and drag anywhere on the widget background or timer label to place it anywhere on your screen.

---

## How to Record While Playing Aion

1. **Launch Aion** (Borderless Windowed or Windowed mode recommended for overlay visibility).
2. **Start Recording**:
   - Click `⚪ REC` on the QuickClip HUD when combat or an epic moment begins.
   - The HUD transforms to `⏹ STOP` with a live red timer counting elapsed time (`MM:SS`).
   - QuickClip triggers the Windows GameDVR recording shortcut without minimizing or defocusing your game.
3. **Stop & Convert**:
   - Click `⏹ STOP` when the action ends.
   - The widget displays `⏳ Criando...` while the video conversion runs asynchronously in the background.
   - Gameplay remains completely smooth and responsive—the UI never freezes.
4. **View Your Short**:
   - When processing completes, QuickClip automatically opens Windows Explorer highlighting the rendered file.
   - The HUD returns to `⚪ REC / Pronto` ready for your next clip.
   - Click `📁` anytime to open the `output/shorts/` folder.

---

## Output Specifications

| Property | Value |
|---|---|
| **Resolution** | 1080 x 1920 (9:16 Vertical Video) |
| **Foreground Video** | 1080 x 608 uncropped native aspect ratio (centered) |
| **Background** | 1080 x 1920 scaled, cropped, and blurred (`boxblur=luma_radius=20:luma_power=2`) |
| **Video Codec** | H.264 (libx264) with `fast` preset and CRF 22 |
| **Audio** | AAC stereo 192kbps |
| **Save Location** | `output/shorts/short_YYYYMMDD_HHMMSS.mp4` |

---

## Project Structure

```
quickclip/
├── quickclip/
│   ├── app.py           # Application entrypoint & pipeline orchestrator
│   ├── capture.py       # GameDVR trigger, file watcher & detection
│   ├── config.py        # Config paths & environment management
│   ├── processor.py     # FFmpeg 9:16 Shorts converter & filtergraph builder
│   ├── publisher.py     # Windows Explorer & YouTube upload utilities
│   └── ui.py            # Win32 non-activating floating HUD widget
├── tests/               # Comprehensive automated test suite (35 unit tests)
├── output/
│   └── shorts/          # Rendered Shorts destination folder
├── run.bat              # One-click Windows launcher
└── README.md            # User guide & documentation
```

---

## Running Automated Tests

To run the complete test suite:

```bash
python -m pytest tests/ -v
```

All 35 unit tests should execute and pass cleanly.
