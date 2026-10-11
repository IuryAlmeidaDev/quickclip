"""YouTube Data API v3 uploader for QuickClip automated Shorts publishing."""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service(
    client_secrets_file: Path,
    token_file: Path,
    auth_flow_callback: Optional[Callable[[], None]] = None,
) -> Any:
    """Authenticates and returns a YouTube Data API v3 resource.

    If token_file exists and is valid, loads stored OAuth2 credentials.
    If credentials are expired, refreshes them automatically.
    If no valid token exists, initiates OAuth2 flow using client_secrets_file.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials = None

    if token_file.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_file), YOUTUBE_SCOPES)
        except Exception as e:
            logger.warning("Failed to load existing token_file: %s", e)
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(credentials.to_json())
        except Exception as e:
            logger.warning("Failed to refresh credentials: %s", e)
            credentials = None

    if not credentials or not credentials.valid:
        if not client_secrets_file.exists():
            raise FileNotFoundError(
                f"Arquivo client_secrets.json não encontrado em: {client_secrets_file}\n"
                "Para postar direto no YouTube, baixe as credenciais do Google Cloud Console "
                "e coloque o arquivo 'client_secrets.json' na pasta do QuickClip."
            )

        if auth_flow_callback:
            auth_flow_callback()

        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_file), YOUTUBE_SCOPES
        )
        credentials = flow.run_local_server(port=0, prompt="consent")

        with open(token_file, "w", encoding="utf-8") as f:
            f.write(credentials.to_json())

    return build("youtube", "v3", credentials=credentials)


def upload_short_video(
    video_path: Path,
    client_secrets_file: Path,
    token_file: Path,
    title: str = "AION 2 — Batalha Épica! #Shorts",
    description: str = "Gameplay frenética gravada com QuickClip! #Shorts #AION2 #MMORPG #Gaming",
    tags: Optional[List[str]] = None,
    privacy_status: str = "public",
    progress_callback: Optional[Callable[[int], None]] = None,
    auth_flow_callback: Optional[Callable[[], None]] = None,
) -> Dict[str, str]:
    """Uploads a video to YouTube as a vertical Short using YouTube Data API v3.

    Returns dict with 'id' and 'url' of the published video.
    """
    from googleapiclient.http import MediaFileUpload

    if not video_path.exists():
        raise FileNotFoundError(f"Vídeo para upload não encontrado: {video_path}")

    if tags is None:
        tags = ["Shorts", "AION2", "Aion", "MMORPG", "Gaming"]

    youtube = get_authenticated_service(
        client_secrets_file=client_secrets_file,
        token_file=token_file,
        auth_flow_callback=auth_flow_callback,
    )

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "20",  # 20 = Gaming
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 2,  # 2MB chunks
    )

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and progress_callback:
            percent = int(status.progress() * 100)
            progress_callback(percent)

    video_id = response.get("id", "")
    short_url = f"https://youtube.com/shorts/{video_id}" if video_id else ""

    logger.info("Vídeo postado com sucesso no YouTube: %s", short_url)
    return {"id": video_id, "url": short_url}
