from pathlib import Path
from quickclip.config import get_config, Config

def test_config_paths():
    cfg = get_config()
    assert isinstance(cfg, Config)
    assert Path(cfg.captures_dir).exists()
    assert Path(cfg.ffmpeg_bin).exists()
    assert Path(cfg.output_dir).name == "shorts"
    assert Path(cfg.music_dir).exists()
    assert Path(cfg.music_dir).name == "music"
    assert Path(cfg.base_dir).exists()
    assert cfg.client_secrets_file.name == "client_secrets.json"
    assert cfg.token_file.name == "token.json"


