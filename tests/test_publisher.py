from pathlib import Path
from unittest.mock import patch

from quickclip.publisher import (
    open_output_folder,
    open_youtube_upload,
    prepare_shorts_metadata,
)


def test_prepare_shorts_metadata():
    meta = prepare_shorts_metadata("Aion_Boss_Fight.mp4")
    assert "title" in meta
    assert "description" in meta
    assert "tags" in meta
    assert "#Shorts" in meta["tags"]
    assert "#Aion" in meta["tags"]


def test_open_output_folder_dir(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        open_output_folder(tmp_path)
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert str(tmp_path) in cmd


def test_open_output_folder_file(tmp_path):
    test_file = tmp_path / "clip.mp4"
    test_file.touch()
    with patch("subprocess.Popen") as mock_popen:
        open_output_folder(test_file)
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert "/select," in cmd
        assert str(test_file) in cmd


def test_open_youtube_upload():
    with patch("webbrowser.open") as mock_web_open:
        open_youtube_upload()
        mock_web_open.assert_called_once_with(
            "https://studio.youtube.com/channel/UC/videos/upload?d=ud"
        )
