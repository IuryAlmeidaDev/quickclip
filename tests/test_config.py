from pathlib import Path
from quickclip.config import get_config, Config

def test_config_paths():
    cfg = get_config()
    assert isinstance(cfg, Config)
    assert Path(cfg.captures_dir).exists()
    assert Path(cfg.ffmpeg_bin).exists()
    assert Path(cfg.output_dir).name == "shorts"
