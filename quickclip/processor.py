import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess
import logging
import random

logger = logging.getLogger(__name__)


def _get_subprocess_hidden_kwargs() -> dict:
    """Returns kwargs to ensure background execution without console windows on Windows."""
    kwargs = {}
    if sys.platform == "win32":
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        if hasattr(subprocess, "STARTF_USESHOWWINDOW"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            kwargs["startupinfo"] = startupinfo
    return kwargs



def build_ffmpeg_filter(
    target_width: int = 1080,
    target_height: int = 1920,
    game_title: str = "AION 2",
    subtitle: str = "EPIC BOSS BATTLE",
    title: Optional[str] = None,
) -> str:
    """Build FFmpeg complex filter chain for viral high-retention 9:16 gaming Shorts."""
    # Split into 3 layers:
    # 1. Background: cropped/scaled to 1080x1920 with dark blur
    # 2. Upper half: Action zoom focused on character & boss combat
    # 3. Lower half: Overview gameplay with HUD, health bars, and skills
    # 4. Top header: Obsidian gaming badge with gold double-border & glowing titles
    # 5. Divider: Golden separator line dividing zoom action and HUD overview
    if title is not None:
        subtitle = title

    safe_game = " ".join(game_title.strip().replace("'", "").replace(":", ""))
    safe_sub = subtitle.replace("'", "").replace(":", "")

    box_w = 880
    box_x = (target_width - box_w) // 2
    inner_w = 868
    inner_x = (target_width - inner_w) // 2
    divider_w = 960
    divider_x = (target_width - divider_w) // 2

    header_box = (
        f"drawbox=x={box_x}:y=40:w={box_w}:h=136:color=black@0.78:t=fill,"
        f"drawbox=x={box_x}:y=40:w={box_w}:h=136:color=#F59E0B@0.95:t=3,"
        f"drawbox=x={inner_x}:y=46:w={inner_w}:h=124:color=#B45309@0.5:t=1"
    )
    title_text = (
        f"drawtext=text='—  {safe_game}  —':fontsize=30:fontcolor=#FDE047:"
        "x=(w-text_w)/2:y=56:shadowcolor=black@0.9:shadowx=2:shadowy=2"
    )
    sub_text = (
        f"drawtext=text='{safe_sub}':fontsize=54:fontcolor=white:"
        "x=(w-text_w)/2:y=100:borderw=2:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3"
    )
    divider = f"drawbox=x={divider_x}:y=1078:w={divider_w}:h=4:color=#F59E0B@0.75:t=fill"

    return (
        f"[0:v]split=3[bg_raw][zoom_raw][full_raw];"
        f"[bg_raw]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},boxblur=25:5,colorchannelmixer=aa=1:rr=0.4:gg=0.4:bb=0.4[bg];"
        f"[zoom_raw]scale=2300:-2,crop={target_width}:860:(in_w-{target_width})/2:(in_h-860)/2[zoom_act];"
        f"[full_raw]scale={target_width}:-2[full_game];"
        f"[bg][zoom_act]overlay=0:200[v1];"
        f"[v1][full_game]overlay=0:1100[v2];"
        f"[v2]{header_box},{title_text},{sub_text},{divider}[outv]"
    )



def generate_output_filename(source_filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_stem = Path(source_filename).stem.replace(" ", "_")
    return f"{clean_stem}_{timestamp}_short.mp4"


def get_random_music_track(music_dir: Optional[Path]) -> Optional[Path]:
    """Finds a random royalty-free music file in music_dir if available."""
    if not music_dir or not music_dir.exists():
        return None
    valid_exts = {".mp3", ".wav", ".ogg", ".aac", ".m4a"}
    music_files = [f for f in music_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
    if not music_files:
        return None
    return random.choice(music_files)


def has_audio_stream(input_path: Path, ffmpeg_bin: Path) -> bool:
    """Checks whether the source video contains an audio stream."""
    try:
        cmd = [str(ffmpeg_bin), "-i", str(input_path)]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **_get_subprocess_hidden_kwargs(),
        )
        return "Audio:" in res.stderr
    except Exception:
        return False


def convert_to_shorts(
    input_path: Path,
    output_dir: Path,
    ffmpeg_bin: Path,
    music_dir: Optional[Path] = None,
    game_title: str = "AION 2",
    subtitle: str = "EPIC BOSS BATTLE",
    title: Optional[str] = None,
) -> Path:
    """Converts input gameplay into a viral, high-retention 1080x1920 9:16 Short with audio mix."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = generate_output_filename(input_path.name)
    output_path = output_dir / out_name

    filter_v = build_ffmpeg_filter(1080, 1920, game_title=game_title, subtitle=subtitle, title=title)
    music_track = get_random_music_track(music_dir)
    has_game_audio = has_audio_stream(input_path, ffmpeg_bin)

    cmd = [str(ffmpeg_bin), "-y", "-i", str(input_path)]

    if music_track:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_track)])

        if has_game_audio:
            filter_a = (
                "[0:a]volume=1.0[game_a];"
                "[1:a]volume=0.30[music_a];"
                "[game_a][music_a]amix=inputs=2:duration=first:dropout_transition=2[outa]"
            )
            filter_complex = f"{filter_v};{filter_a}"
            map_audio = ["[outa]"]
        else:
            filter_a = "[1:a]volume=0.75[outa]"
            filter_complex = f"{filter_v};{filter_a}"
            map_audio = ["[outa]"]
    else:
        filter_complex = filter_v
        map_audio = ["0:a?"]

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
    ])

    if map_audio:
        cmd.extend(["-map", map_audio[0]])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "17",
        "-c:a", "aac",
        "-b:a", "256k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ])

    logger.info("Executing FFmpeg viral shorts conversion: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **_get_subprocess_hidden_kwargs(),
    )
    if result.returncode != 0:
        logger.error("FFmpeg error: %s", result.stderr)
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}: {result.stderr[-500:]}")

    return output_path
