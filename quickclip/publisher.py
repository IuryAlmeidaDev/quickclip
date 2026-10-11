"""Publisher and output management utilities for QuickClip."""

import subprocess
import webbrowser
from pathlib import Path
from typing import Any, Dict, Union


def prepare_shorts_metadata(video_name: str) -> Dict[str, Any]:
    """Generates suggested metadata (title, description, tags) for YouTube Shorts."""
    return {
        "title": "AION 2 Gameplay Highlight #Shorts",
        "description": "Momentos insanos de AION 2! #AION2 #Aion #MMORPG #Shorts #Gaming",
        "tags": ["#Shorts", "#AION2", "#Aion", "#MMORPG", "#Gaming"],
    }


def open_output_folder(path: Union[Path, str]) -> None:
    """Opens Windows Explorer focused on the specified file or directory."""
    target_path = Path(path)
    folder = target_path if target_path.is_dir() else target_path.parent
    if target_path.is_file():
        subprocess.Popen(f'explorer /select,"{target_path}"')
    else:
        subprocess.Popen(f'explorer "{folder}"')


def open_youtube_upload() -> None:
    """Opens the YouTube Studio upload page in the default web browser."""
    webbrowser.open("https://studio.youtube.com/channel/UC/videos/upload?d=ud")
