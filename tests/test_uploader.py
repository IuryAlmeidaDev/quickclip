from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from quickclip.uploader import get_authenticated_service, upload_short_video


def test_get_authenticated_service_missing_secrets(tmp_path):
    secrets = tmp_path / "missing_secrets.json"
    token = tmp_path / "missing_token.json"

    with pytest.raises(FileNotFoundError, match="client_secrets.json"):
        get_authenticated_service(secrets, token)


@patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
@patch("googleapiclient.discovery.build")
def test_get_authenticated_service_valid_token(mock_build, mock_from_file, tmp_path):
    secrets = tmp_path / "secrets.json"
    token = tmp_path / "token.json"
    token.write_text('{"token": "dummy"}')

    mock_creds = MagicMock()
    mock_creds.expired = False
    mock_creds.valid = True
    mock_from_file.return_value = mock_creds

    service = get_authenticated_service(secrets, token)
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
    assert service == mock_build.return_value


@patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
@patch("googleapiclient.discovery.build")
def test_get_authenticated_service_refresh_token(mock_build, mock_from_file, tmp_path):
    secrets = tmp_path / "secrets.json"
    token = tmp_path / "token.json"
    token.write_text('{"token": "dummy"}')

    mock_creds = MagicMock()
    mock_creds.expired = True
    mock_creds.refresh_token = "refresh_dummy"
    mock_creds.valid = True
    mock_creds.to_json.return_value = '{"token": "refreshed"}'
    mock_from_file.return_value = mock_creds

    service = get_authenticated_service(secrets, token)
    mock_creds.refresh.assert_called_once()
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
    assert service == mock_build.return_value


@patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file")
@patch("googleapiclient.discovery.build")
def test_get_authenticated_service_flow(mock_build, mock_flow_cls, tmp_path):
    secrets = tmp_path / "client_secrets.json"
    secrets.write_text('{"installed": {}}')
    token = tmp_path / "token.json"

    mock_flow = MagicMock()
    mock_creds = MagicMock(valid=True)
    mock_creds.to_json.return_value = '{"token": "new"}'
    mock_flow.run_local_server.return_value = mock_creds
    mock_flow_cls.return_value = mock_flow

    callback = MagicMock()
    service = get_authenticated_service(secrets, token, auth_flow_callback=callback)

    callback.assert_called_once()
    mock_flow.run_local_server.assert_called_once()
    assert token.exists()
    assert token.read_text() == '{"token": "new"}'
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)


def test_upload_short_video_file_not_found(tmp_path):
    video = tmp_path / "nonexistent.mp4"
    secrets = tmp_path / "secrets.json"
    token = tmp_path / "token.json"

    with pytest.raises(FileNotFoundError, match="Vídeo para upload não encontrado"):
        upload_short_video(video, secrets, token)


@patch("quickclip.uploader.get_authenticated_service")
@patch("googleapiclient.http.MediaFileUpload")
def test_upload_short_video_success(mock_media_cls, mock_get_service, tmp_path):
    video = tmp_path / "gameplay_short.mp4"
    video.write_bytes(b"dummy mp4")
    secrets = tmp_path / "secrets.json"
    token = tmp_path / "token.json"

    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_request = MagicMock()
    status_mock = MagicMock()
    status_mock.progress.return_value = 0.5
    mock_request.next_chunk.side_effect = [
        (status_mock, None),
        (None, {"id": "TEST_SHORTS_123"}),
    ]

    mock_service.videos().insert.return_value = mock_request

    progress_calls = []
    def on_progress(p):
        progress_calls.append(p)

    res = upload_short_video(
        video,
        secrets,
        token,
        title="Custom Aion Short",
        description="Epic PVP",
        tags=["#Aion2", "#PVP"],
        progress_callback=on_progress,
    )

    assert res["id"] == "TEST_SHORTS_123"
    assert res["url"] == "https://youtube.com/shorts/TEST_SHORTS_123"
    assert progress_calls == [50]
