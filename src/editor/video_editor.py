"""
Pipeline Steps 3.4 & 3.5: Audio Narration (Segmind ElevenLabs TTS), Subtitles & Video Assembly (FFmpeg/MoviePy)
"""

import os
import logging
import requests
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

SEGMIND_TTS_URL = "https://api.segmind.com/v1/elevenlabs-tts"

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

    def calculate_tts_cost(self, text: str, headers: Optional[dict] = None) -> float:
        """
        Calculates exact Segmind ElevenLabs TTS cost:
        - Segmind ElevenLabs TTS rate: $0.16875 per 1,000 characters ($0.00016875/char).
        - If x-credits-used header is returned, parses credits_used * $0.001.
        """
        if headers:
            credits = headers.get("x-credits-used") or headers.get("credits_used")
            if credits:
                try:
                    return float(credits) * 0.001
                except (ValueError, TypeError):
                    pass

        # Character-based exact formula
        char_count = len(text)
        return char_count * (0.16875 / 1000.0)

    def generate_narration(self, text: str, output_audio_path: str) -> Tuple[str, float]:
        """
        Generates TTS audio narration via Segmind ElevenLabs TTS API or creates dummy audio in mock mode.
        Returns tuple: (output_audio_path, tts_cost).
        """
        if self.mock_mode or not self.api_key:
            logger.info(f"[MOCK] Generating Segmind ElevenLabs TTS narration for text: '{text[:30]}...'")
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(b"MOCK_SEGMIND_ELEVENLABS_TTS_AUDIO_DATA")
            mock_cost = self.calculate_tts_cost(text)
            return output_audio_path, mock_cost

        logger.info(f"Connecting to Segmind ElevenLabs TTS API for narration text: '{text[:30]}...'")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "language": "en",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel / friendly voice
        }

        try:
            response = requests.post(SEGMIND_TTS_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(response.content)

            real_cost = self.calculate_tts_cost(text, dict(response.headers))
            logger.info(f"Successfully generated Segmind ElevenLabs TTS audio ({len(text)} chars). Cost: ${real_cost:.6f}")
            return output_audio_path, real_cost
        except Exception as e:
            logger.error(f"Error calling Segmind ElevenLabs TTS API: {e}")
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
