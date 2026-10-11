from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from quickclip.processor import (
    build_ffmpeg_filter,
    generate_output_filename,
    get_random_music_track,
    has_audio_stream,
    convert_to_shorts,
)


def test_build_ffmpeg_filter():
    filter_chain = build_ffmpeg_filter(target_width=1080, target_height=1920, title="AION BOSS BATTLE")
    assert "split=3" in filter_chain
    assert "boxblur=25:5" in filter_chain
    assert "zoom_act" in filter_chain
    assert "full_game" in filter_chain
    assert "overlay" in filter_chain
    assert "drawtext" in filter_chain
    assert "AION BOSS BATTLE" in filter_chain


def test_generate_output_filename():
    name = generate_output_filename("Aion_2026.mp4")
    assert name.endswith(".mp4")
    assert "short" in name
    assert "Aion_2026" in name


def test_get_random_music_track_empty_or_none(tmp_path):
    assert get_random_music_track(None) is None
    empty_dir = tmp_path / "empty_music"
    empty_dir.mkdir()
    assert get_random_music_track(empty_dir) is None


def test_get_random_music_track_success(tmp_path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    track1 = music_dir / "battle1.mp3"
    track1.write_bytes(b"dummy mp3")
    ignored = music_dir / "notes.txt"
    ignored.write_text("not audio")

    selected = get_random_music_track(music_dir)
    assert selected == track1


@patch("subprocess.run")
def test_has_audio_stream(mock_run, tmp_path):
    test_video = tmp_path / "test.mp4"
    test_video.write_text("data")
    ffmpeg = Path("ffmpeg")

    mock_run.return_value = MagicMock(stderr="Stream #0:1: Audio: aac (LC)")
    assert has_audio_stream(test_video, ffmpeg) is True

    mock_run.return_value = MagicMock(stderr="Stream #0:0: Video: h264")
    assert has_audio_stream(test_video, ffmpeg) is False


def test_convert_to_shorts_file_not_found(tmp_path):
    non_existent = tmp_path / "missing.mp4"
    output_dir = tmp_path / "output"
    ffmpeg_bin = Path("ffmpeg")
    with pytest.raises(FileNotFoundError):
        convert_to_shorts(non_existent, output_dir, ffmpeg_bin)


@patch("quickclip.processor.has_audio_stream", return_value=True)
@patch("subprocess.run")
def test_convert_to_shorts_with_music(mock_run, mock_has_audio, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    input_file = tmp_path / "video.mp4"
    input_file.write_text("dummy")
    output_dir = tmp_path / "shorts"
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    music_file = music_dir / "epic.mp3"
    music_file.write_bytes(b"audio")
    ffmpeg_bin = Path("ffmpeg")

    result_path = convert_to_shorts(input_file, output_dir, ffmpeg_bin, music_dir=music_dir)

    assert result_path.parent == output_dir
    assert result_path.name.endswith(".mp4")
    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "-stream_loop" in cmd
    assert str(music_file) in cmd
    assert "-crf" in cmd
    assert "17" in cmd
    assert "-pix_fmt" in cmd
    assert "yuv420p" in cmd
    assert "-movflags" in cmd
    assert "+faststart" in cmd


@patch("quickclip.processor.has_audio_stream", return_value=False)
@patch("subprocess.run")
def test_convert_to_shorts_no_music(mock_run, mock_has_audio, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    input_file = tmp_path / "video.mp4"
    input_file.write_text("dummy")
    output_dir = tmp_path / "shorts"
    ffmpeg_bin = Path("ffmpeg")

    result_path = convert_to_shorts(input_file, output_dir, ffmpeg_bin, music_dir=None)

    assert result_path.parent == output_dir
    cmd = mock_run.call_args[0][0]
    assert "-stream_loop" not in cmd
    assert "-crf" in cmd
    assert "17" in cmd


@patch("subprocess.run")
def test_convert_to_shorts_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="FFmpeg syntax error")
    input_file = tmp_path / "video.mp4"
    input_file.write_text("dummy")
    output_dir = tmp_path / "shorts"
    ffmpeg_bin = Path("ffmpeg")

    with pytest.raises(RuntimeError, match="FFmpeg failed with code 1"):
        convert_to_shorts(input_file, output_dir, ffmpeg_bin)
