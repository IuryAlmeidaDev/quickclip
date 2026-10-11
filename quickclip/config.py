import sys
from dataclasses import dataclass
from pathlib import Path
import imageio_ffmpeg

@dataclass(frozen=True)
class Config:
    captures_dir: Path
    output_dir: Path
    music_dir: Path
    ffmpeg_bin: Path
    base_dir: Path
    client_secrets_file: Path
    token_file: Path

def get_config() -> Config:
    user_home = Path.home()
    captures_dir = user_home / "Videos" / "Captures"
    if not captures_dir.exists():
        captures_dir.mkdir(parents=True, exist_ok=True)

    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent.parent

    output_dir = base_dir / "output" / "shorts"
    output_dir.mkdir(parents=True, exist_ok=True)

    music_dir = base_dir / "assets" / "music"
    music_dir.mkdir(parents=True, exist_ok=True)

    try:
        ffmpeg_bin = Path(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        ffmpeg_bin = Path(getattr(sys, "_MEIPASS", ".")) / "ffmpeg.exe"

    return Config(
        captures_dir=captures_dir,
        output_dir=output_dir,
        music_dir=music_dir,
        ffmpeg_bin=ffmpeg_bin,
        base_dir=base_dir,
        client_secrets_file=base_dir / "client_secrets.json",
        token_file=base_dir / "token.json",
    )

