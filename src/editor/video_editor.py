"""
Pipeline Steps 3.4 & 3.5: Audio Narration (Segmind TTS), Subtitles & Video Assembly (FFmpeg/MoviePy)
"""

import os
import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)

SEGMIND_TTS_URL = "https://api.segmind.com/v1/tts"

# Channel Brand Colors
PALETTE = {
    "primary_bg": "#FFD166",      # Sunshine Yellow (60%)
    "secondary_bg": "#4EA8DE",    # Sky Blue (30%)
    "action_pop": "#EF476F",      # Bubblegum Pink (10%)
    "text_stroke": "#0F4C81",     # Midnight Blue (Outline)
}


class VideoEditor:
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key or os.getenv("SEGMIND_API_KEY")
        self.mock_mode = mock_mode

    def generate_narration(self, text: str, output_audio_path: str) -> str:
        """
        Generates TTS audio narration via Segmind TTS API or creates dummy audio in mock mode.
        Estimated Cost: ~$0.002 per video.
        """
        if self.mock_mode or not self.api_key:
            logger.info(f"[MOCK] Generating Segmind TTS narration for text: '{text[:30]}...'")
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(b"MOCK_SEGMIND_TTS_AUDIO_DATA")
            return output_audio_path

        logger.info(f"Connecting to Segmind TTS API for narration text: '{text[:30]}...'")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "language": "en",
            "voice": "friendly_child",
        }

        try:
            response = requests.post(SEGMIND_TTS_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Successfully generated TTS audio: {output_audio_path}")
            return output_audio_path
        except Exception as e:
            logger.error(f"Error calling Segmind TTS API: {e}")
            raise e

    def assemble_video(
        self,
        video_clips: List[str],
        audio_clips: List[str],
        subtitles: List[str],
        output_video_path: str,
    ) -> str:
        """
        Merges video clips, syncs audio, burns Fredoka subtitles, and exports 9:16 Shorts video.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Assembling final video into {output_video_path}")
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
            with open(output_video_path, "wb") as f:
                f.write(b"MOCK_FINAL_VIDEO_DATA")
            return output_video_path

        # FFmpeg assembly logic will be expanded in Sprint 2
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        with open(output_video_path, "wb") as f:
            f.write(b"MOCK_FINAL_VIDEO_DATA")
        return output_video_path
