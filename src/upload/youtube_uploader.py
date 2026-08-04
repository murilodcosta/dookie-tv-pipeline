"""
YouTube Data API v3 OAuth2 Uploader for publishing approved Shorts.
Supports OAuth2 authentication flow, credentials caching, and madeForKids=True setting.
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(
        self,
        client_secret_file: Optional[str] = None,
        credentials_file: Optional[str] = None,
        mock_mode: bool = True,
    ):
        self.client_secret_file = client_secret_file or os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "config/client_secret.json")
        self.credentials_file = credentials_file or os.getenv("YOUTUBE_CREDENTIALS_FILE", "config/youtube_oauth2.json")
        self.mock_mode = mock_mode

    def get_authenticated_service(self):
        """
        Authenticates with YouTube Data API v3 via OAuth2 and returns an authorized service client.
        Caches authorized tokens in config/youtube_oauth2.json.
        """
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        if os.path.exists(self.credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(self.credentials_file, YOUTUBE_UPLOAD_SCOPE)
            except Exception as e:
                logger.warning(f"Failed to load cached credentials ({e}). Re-authenticating...")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired YouTube OAuth2 access token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError(
                        f"OAuth2 client secret file not found at '{self.client_secret_file}'. "
                        "Please download client_secret.json from Google Cloud Console and place it in config/."
                    )
                logger.info(f"Initiating browser OAuth2 flow using '{self.client_secret_file}'...")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, YOUTUBE_UPLOAD_SCOPE)
                creds = flow.run_local_server(port=0)

            # Save authorized credentials for future runs
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            logger.info(f"Saved OAuth2 credentials to '{self.credentials_file}'.")

        return build("youtube", "v3", credentials=creds)

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "unlisted",
    ) -> str:
        """
        Uploads an approved Short to YouTube with madeForKids=True setting.
        Returns YouTube Short public URL.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Uploaded video '{title}' to YouTube (privacyStatus={privacy_status}, madeForKids=True).")
            return "https://youtube.com/shorts/mock_video_id_123"

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found for YouTube upload: {video_path}")

        logger.info(f"Connecting to YouTube Data API v3 to upload Short '{title}' (privacyStatus={privacy_status})...")
        youtube = self.get_authenticated_service()

        from googleapiclient.http import MediaFileUpload

        body = {
            "snippet": {
                "title": title[:100],  # Title under 100 chars
                "description": description,
                "tags": tags,
                "categoryId": "27",  # Education category
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": True,
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        logger.info(f"Uploading video file ({os.path.getsize(video_path)} bytes) to YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%...")

        video_id = response.get("id")
        youtube_url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"✅ Video uploaded successfully! Published YouTube Short URL: {youtube_url}")
        return youtube_url
