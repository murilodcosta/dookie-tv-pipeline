"""
Video Editor module for audio sync, Fredoka subtitle burn-in, and final video assembly.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# Channel Brand Colors
PALETTE = {
    "primary_bg": "#FFD166",      # Sunshine Yellow (60%)
    "secondary_bg": "#4EA8DE",    # Sky Blue (30%)
    "action_pop": "#EF476F",      # Bubblegum Pink (10%)
    "text_stroke": "#0F4C81",     # Midnight Blue (Outline)
}


class VideoEditor:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    def generate_narration(self, text: str, output_audio_path: str) -> str:
        """
        Generates TTS audio via Segmind TTS API or mock audio file.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Generating TTS narration for text: '{text[:30]}...'")
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(b"MOCK_AUDIO_DATA")
            return output_audio_path

        raise NotImplementedError("Real Segmind TTS API call not configured yet.")

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

        raise NotImplementedError("Real FFmpeg assembly not implemented yet.")
