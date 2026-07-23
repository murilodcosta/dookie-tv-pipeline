"""
YouTube Data API v3 OAuth2 Uploader for publishing approved Shorts.
"""

import logging

logger = logging.getLogger(__name__)


class YouTubeUploader:
    def __init__(self, client_secret_file: str | None = None, mock_mode: bool = True):
        self.client_secret_file = client_secret_file
        self.mock_mode = mock_mode

    def upload_short(self, video_path: str, title: str, description: str, tags: list[str]) -> str:
        """
        Uploads an approved Short to YouTube with madeForKids=True setting.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Uploaded video '{title}' to YouTube (madeForKids=True).")
            return "https://youtube.com/shorts/mock_video_id_123"

        raise NotImplementedError("Real YouTube Data API OAuth2 uploader not configured yet.")
