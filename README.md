# QuickClip 🎬

**QuickClip** is a lightweight, zero-distraction desktop tool designed for gamers to instantly record gameplay highlights (optimized for *Aion* and other PC games) and automatically produce vertical YouTube Shorts (1080x1920, 9:16) with blurred backgrounds in one seamless click.

---

## Key Features

- **One-Click Recording**: Start and stop recordings directly from an unobtrusive, always-on-top floating HUD.
- **Accidental Recording Guard**: Quick recordings under 2 seconds are automatically ignored (`Muito curto`), preventing accidental clicks from triggering unnecessary video encoding.
- **No Focus Stealing (`WS_EX_NOACTIVATE`)**: The widget utilizes native Windows API styles so clicking the HUD buttons never steals keyboard or mouse focus from *Aion*, preventing game window minimization or input interruptions.
- **Automated YouTube Shorts Pipeline**:
  - Automatically captures game clips via Windows GameDVR (`Win+Alt+R`).
  - Converts horizontal 16:9 gameplay footage into high-definition vertical 9:16 Shorts (1080x1920).
  - Creates a dynamic blurred and darkened background (`boxblur=20:5`, `colorchannelmixer`) behind centered, crystal-clear 1080p game footage.
  - Encoded with `yuv420p` pixel format and `+faststart` movflags for instant streaming and universal mobile compatibility.
- **Instant Output & Publishing Integration**:
  - Output clips are automatically saved to `output/shorts/` with clean timestamps (`<name>_YYYYMMDD_HHMMSS_short.mp4`).
  - Automatically opens Windows Explorer highlighting newly rendered videos.
  - Dedicated folder button (`📁`) on the widget to open the shorts directory at any time.
  - Direct YouTube button (`▶`) to instantly open YouTube Studio's upload modal in your default browser.

---

## Requirements

1. **Windows 10 / 11** with **Xbox Game Bar / GameDVR** enabled (default shortcut: `Win + Alt + R`).
2. **Python 3.10+** (Python 3.12 recommended).
3. **FFmpeg** installed and accessible via system `PATH` (or auto-provided by `imageio-ffmpeg`).
4. Python dependencies in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

---

## Getting Started

### 1. Launching QuickClip

You can launch QuickClip in either of two ways:

- **Option A (Recommended)**: Double-click `run.bat` in the project root.
- **Option B (Terminal)**:
  ```bash
  python -m quickclip.app
  ```

Once launched, a compact, dark-mode floating HUD appears on your screen:

```
+---------------------------------------+
|  ⚪ REC    00:00              ▶   📁  |
+---------------------------------------+
```

- **Drag to Move**: Click and drag anywhere on the widget background or timer label to place it anywhere on your screen.
- **▶ Button**: Open YouTube Studio upload directly in your default browser.
- **📁 Button**: Open the `output/shorts/` folder in Windows Explorer.

---

## How to Record While Playing Aion

1. **Launch Aion** (Borderless Windowed or Windowed mode recommended for overlay visibility).
2. **Start Recording**:
   - Click `⚪ REC` on the QuickClip HUD when combat or an epic moment begins.
   - The HUD transforms to `⏹ STOP` with a live red timer counting elapsed time (`MM:SS`).
   - QuickClip triggers the Windows GameDVR recording shortcut without minimizing or defocusing your game.
3. **Stop & Convert**:
   - Click `⏹ STOP` when the action ends.
   - If recorded for less than 2 seconds, the recording is safely ignored (`Muito curto`).
   - Otherwise, the widget displays `⏳ Criando...` while video conversion runs asynchronously in the background.
   - Gameplay remains completely smooth and responsive—the UI never freezes.
4. **Publish Your Short**:
   - When processing completes, QuickClip automatically opens Windows Explorer highlighting the rendered file.
   - Click `▶` on the HUD to jump straight to YouTube Studio's upload page.
   - The HUD returns to `⚪ REC / Pronto` ready for your next clip.

---

## Output Specifications

| Property | Value |
|---|---|
| **Resolution** | 1080 x 1920 (9:16 Vertical Video) |
| **Foreground Video** | 1080px wide centered uncropped native aspect ratio |
| **Background** | 1080 x 1920 scaled, cropped, blurred, and darkened (`boxblur=20:5,colorchannelmixer=aa=1:rr=0.7:gg=0.7:bb=0.7`) |
| **Video Codec** | H.264 (libx264) with `veryfast` preset and CRF 20 |
| **Pixel Format & Flags**| `yuv420p`, `-movflags +faststart` (universal mobile streaming compatibility) |
| **Audio** | AAC stereo 192kbps |
| **Save Location** | `output/shorts/<name>_YYYYMMDD_HHMMSS_short.mp4` |

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
├── tests/               # Comprehensive automated test suite (37 unit tests)
├── output/
│   └── shorts/          # Rendered Shorts destination folder
├── requirements.txt     # Project dependencies
├── run.bat              # One-click Windows launcher
└── README.md            # User guide & documentation
```

---

## Running Automated Tests

To run the complete test suite:

```bash
python -m pytest tests/ -v
```

All 37 unit tests should execute and pass cleanly.
