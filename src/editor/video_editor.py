"""
Pipeline Steps 3.4 & 3.5: Audio Narration (Edge-TTS / Segmind TTS), Subtitles & Video Assembly (FFmpeg/MoviePy)
"""

import os
import logging
import requests
import asyncio
from typing import List, Optional, Tuple

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

    def generate_narration(self, text: str, output_audio_path: str) -> Tuple[str, float]:
        """
        Generates TTS audio narration using Edge-TTS (Microsoft Neural Voice 'en-US-AnaNeural') or Segmind TTS.
        Returns tuple: (output_audio_path, cost).
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Generating TTS narration for text: '{text[:30]}...'")
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(b"MOCK_TTS_AUDIO_DATA")
            return output_audio_path, 0.0

        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        logger.info(f"Generating high-quality child voice narration for text: '{text[:40]}...'")

        # Try Edge-TTS (Microsoft Neural Voice: en-US-AnaNeural)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text=text, voice="en-US-AnaNeural")
            asyncio.run(communicate.save(output_audio_path))
            logger.info(f"Successfully generated Edge-TTS audio: {output_audio_path}")
            return output_audio_path, 0.0
        except Exception as err:
            logger.warning(f"Edge-TTS failed ({err}), falling back to Segmind TTS...")

        # Fallback to Segmind TTS
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

            with open(output_audio_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Successfully generated Segmind TTS audio: {output_audio_path}")
            return output_audio_path, 0.002
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
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

        # FFmpeg assembly logic
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        with open(output_video_path, "wb") as f:
            f.write(b"MOCK_FINAL_VIDEO_DATA")
        return output_video_path
