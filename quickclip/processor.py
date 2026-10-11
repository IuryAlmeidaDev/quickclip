from pathlib import Path
from datetime import datetime
import subprocess
import logging

logger = logging.getLogger(__name__)


def build_ffmpeg_filter(target_width: int = 1080, target_height: int = 1920) -> str:
    """Build FFmpeg complex filter chain for 9:16 Shorts with blurred background."""
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
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    logger.info("Executing FFmpeg conversion: %s", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg error: %s", result.stderr)
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}: {result.stderr[-500:]}")

    return output_path
