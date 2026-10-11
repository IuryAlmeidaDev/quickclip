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
