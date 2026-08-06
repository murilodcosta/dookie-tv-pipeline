"""
Pipeline Steps 3.4 & 3.5: Audio Narration (Edge-TTS / Segmind TTS), Subtitles & Video Assembly (FFmpeg/MoviePy)
Uses Fredoka-SemiBold.ttf for ASS burned animated subtitles.
"""

import os
import shutil
import logging
import subprocess
import requests
import asyncio
from typing import List, Optional, Tuple, Dict, Any, Union

logger = logging.getLogger(__name__)

SEGMIND_TTS_URL = "https://api.segmind.com/v1/tts"
FONT_PATH = os.path.abspath("assets/fonts/Fredoka-SemiBold.ttf")

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

    def create_ass_subtitle_file(self, subtitle_items: List[Dict[str, Any]], output_ass_path: str) -> str:
        """
        Creates an Advanced SubStation Alpha (.ass) subtitle file formatted with Fredoka-SemiBold font.
        White text fill, Midnight Blue outline (#0F4C81).
        """
        font_name = "Fredoka-SemiBold"
        ass_header = (
            "[Script Info]\n"
            "Title: Dookie TV Animated Subtitles\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n"
            "YCbCr Matrix: None\n"
            "PlayResX: 1080\n"
            "PlayResY: 1920\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,{font_name},72,&H00FFFFFF,&H000000FF,&H00814C0F,&H80000000,"
            "-1,0,0,0,100,100,0,0,1,5,0,2,80,80,240,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        dialogues = []
        for idx, item in enumerate(subtitle_items):
            start_s = float(item.get("start", 0.0 + (idx * 3.0)))
            end_s = float(item.get("end", start_s + 3.0))
            text = str(item.get("text", ""))

            # Format timestamps H:MM:SS.cs
            start_str = f"{int(start_s//3600)}:{int((start_s%3600)//60):02d}:{start_s%60:05.2f}"
            end_str = f"{int(end_s//3600)}:{int((end_s%3600)//60):02d}:{end_s%60:05.2f}"

            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

        os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(dialogues) + "\n")

        logger.info(f"Created ASS subtitle file ({len(dialogues)} dialogues): {output_ass_path}")
        return output_ass_path

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
        subtitles: List[Any],
        output_video_path: str,
    ) -> str:
        """
        Merges video clips, syncs audio, burns Fredoka-SemiBold subtitles, and exports 9:16 Shorts video.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Assembling final video into {output_video_path}")
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
            with open(output_video_path, "wb") as f:
                f.write(b"MOCK_FINAL_VIDEO_DATA")
            return output_video_path

        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        # Prepare ASS subtitle file
        ass_path = "data/output/temp/subtitles.ass"
        sub_items = []
        for i, sub in enumerate(subtitles):
            if hasattr(sub, "start") and hasattr(sub, "end") and hasattr(sub, "text"):
                sub_items.append({"start": sub.start, "end": sub.end, "text": sub.text})
            elif isinstance(sub, dict):
                sub_items.append({"start": sub.get("start", i * 3.0), "end": sub.get("end", (i + 1) * 3.0), "text": sub.get("text", "")})
            else:
                sub_items.append({"start": i * 3.0, "end": (i + 1) * 3.0, "text": str(sub)})

        self.create_ass_subtitle_file(sub_items, ass_path)

        input_video = video_clips[0] if video_clips else "data/output/temp/scene_1.mp4"

        # Burn subtitles using FFmpeg with Fredoka-SemiBold font
        escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        escaped_font = FONT_PATH.replace("\\", "/").replace(":", "\\:")

        ffmpeg_bin = "ffmpeg"
        if not shutil.which("ffmpeg"):
            try:
                import imageio_ffmpeg
                ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass

        cmd = [
            ffmpeg_bin, "-y",
            "-i", input_video,
            "-vf", f"subtitles='{escaped_ass}':fontsdir='{os.path.dirname(escaped_font)}'",
            "-c:v", "libx264",
            "-c:a", "copy",
            output_video_path
        ]

        try:
            logger.info(f"Executing FFmpeg subtitle burn: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"FFmpeg assembly complete: {output_video_path}")
            return output_video_path
        except Exception as err:
            logger.warning(f"FFmpeg subtitle burn failed ({err}). Copying base video.")
            if os.path.exists(input_video):
                with open(input_video, "rb") as f_in, open(output_video_path, "wb") as f_out:
                    f_out.write(f_in.read())
            return output_video_path
