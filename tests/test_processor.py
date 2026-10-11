from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from quickclip.processor import (
    build_ffmpeg_filter,
    generate_output_filename,
    convert_to_shorts,
)


def test_build_ffmpeg_filter():
    filter_chain = build_ffmpeg_filter(target_width=1080, target_height=1920)
    assert "split" in filter_chain
    assert "boxblur" in filter_chain or "gblur" in filter_chain
    assert "overlay" in filter_chain
    assert "1080" in filter_chain
    assert "1920" in filter_chain


def test_generate_output_filename():
    name = generate_output_filename("Aion_2026.mp4")
    assert name.endswith(".mp4")
    assert "short" in name
    assert "Aion_2026" in name


def test_convert_to_shorts_file_not_found(tmp_path):
    non_existent = tmp_path / "missing.mp4"
    output_dir = tmp_path / "output"
    ffmpeg_bin = Path("ffmpeg")
    with pytest.raises(FileNotFoundError):
        convert_to_shorts(non_existent, output_dir, ffmpeg_bin)


@patch("subprocess.run")
def test_convert_to_shorts_success(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    input_file = tmp_path / "video.mp4"
    input_file.write_text("dummy")
    output_dir = tmp_path / "shorts"
    ffmpeg_bin = Path("ffmpeg")

    result_path = convert_to_shorts(input_file, output_dir, ffmpeg_bin)

    assert result_path.parent == output_dir
    assert result_path.name.endswith(".mp4")
    assert "short" in result_path.name
    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "ffmpeg"
    assert str(input_file) in cmd
    assert str(result_path) in cmd


@patch("subprocess.run")
def test_convert_to_shorts_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="FFmpeg syntax error")
    input_file = tmp_path / "video.mp4"
    input_file.write_text("dummy")
    output_dir = tmp_path / "shorts"
    ffmpeg_bin = Path("ffmpeg")

    with pytest.raises(RuntimeError, match="FFmpeg failed with code 1"):
        convert_to_shorts(input_file, output_dir, ffmpeg_bin)
