"""
Pipeline Steps 3.2 & 3.3: Media Generator via Segmind API (Seedance 2.0)
Generates 9:16 vertical 1080p animation video clips using mascot reference images & reference audios from Cloudflare R2.
"""

import os
import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)

SEGMIND_SEEDANCE_URL = "https://api.segmind.com/v1/seedance-2.0"


class MediaGenerator:
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key or os.getenv("SEGMIND_API_KEY")
        self.mock_mode = mock_mode
        self.r2_public_domain = os.getenv("R2_PUBLIC_DOMAIN", "pub-e726103cf37145cd8aa562e81d9193d2.r2.dev").strip()

    def get_mascot_asset(self, mascot: str) -> str:
        """
        Returns local mascot character asset path.
        """
        filename = f"{mascot.lower()}-character.png"
        path = os.path.join("assets", "mascots", filename)
        if not os.path.exists(path):
            logger.warning(f"Mascot asset not found at {path}, using default dookie-character.png")
            return os.path.join("assets", "mascots", "dookie-character.png")
        return path

    def get_mascot_reference_urls(self, mascot: str) -> List[str]:
        """
        Returns clean public HTTP R2 URLs for mascot reference_images array sent to Segmind Seedance 2.0.
        """
        mascot_clean = mascot.lower()
        base_url = f"https://{self.r2_public_domain}/mascots"
        return [
            f"{base_url}/{mascot_clean}-character.png",
            f"{base_url}/{mascot_clean}-character-sheets.png",
        ]

    def get_reference_audio_urls(self) -> List[str]:
        """
        Returns clean public HTTP R2 URLs for reference_audios array sent to Segmind Seedance 2.0:
        vocal_reference.mp3 and music_reference.mp3.
        """
        base_url = f"https://{self.r2_public_domain}/audio"
        return [
            f"{base_url}/vocal_reference.mp3",
            f"{base_url}/music_reference.mp3",
        ]

    def animate_video(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        mascot: str = "dookie",
        duration: int = 15,
        force_recreate: bool = False,
    ) -> str:
        """
        Calls Segmind Seedance 2.0 API to generate vertical 9:16 Full HD video clip.
        Uses reference_images and reference_audios arrays.
        """
        # LOCAL CREDIT PROTECTION: Skip API call if generated video file exists and is valid!
        if not force_recreate and os.path.exists(output_path) and os.path.getsize(output_path) > 100 * 1024:
            logger.info(f"🛡️ [CACHE HIT] Existing video found at '{output_path}' ({os.path.getsize(output_path)} bytes). Re-using file & skipping Segmind API call to save credits!")
            return output_path

        if self.mock_mode or not self.api_key:
            logger.info(f"[MOCK] Animating asset {image_path} with Seedance multi-shot prompt: '{prompt[:40]}...'")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_SEGMIND_SEEDANCE_VIDEO_DATA")
            return output_path

        logger.info(f"Connecting to Segmind Seedance 2.0 API for mascot '{mascot}' (HD 720p, Multi-Shot 10s, Budget: $1.51 USD)...")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Retrieve public R2 URLs for reference_images and reference_audios arrays
        ref_image_urls = self.get_mascot_reference_urls(mascot)
        ref_audio_urls = self.get_reference_audio_urls()

        # Enforce mascot reference binding in prompt text
        if "image 1" not in prompt.lower():
            styled_prompt = (
                f"{mascot.capitalize()}, the mascot character from image 1 and image 2, "
                "is in 3D Pixar animated cartoon style, stylized cute 3D character, smooth 3D render, NOT realistic photo. "
                f"{prompt}"
            )
        else:
            styled_prompt = prompt

        # Segmind Seedance 2.0 EXACT payload parameters
        payload = {
            "prompt": styled_prompt,
            "duration": 10,
            "resolution": "720p",
            "aspect_ratio": "9:16",
            "generate_audio": True,
            "reference_images": ref_image_urls,
            "reference_audios": ref_audio_urls,
        }

        try:
            logger.info(f"Sending Segmind Seedance 2.0 Payload with reference_images: {ref_image_urls} and reference_audios: {ref_audio_urls}")
            response = requests.post(SEGMIND_SEEDANCE_URL, headers=headers, json=payload, timeout=300)
            if response.status_code != 200:
                logger.error(f"Segmind API returned HTTP {response.status_code}: {response.text}")
            response.raise_for_status()
            
            # Save output binary video stream
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Successfully rendered video clip ({len(response.content)} bytes): {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error calling Segmind Seedance 2.0 API: {e}")
            raise e
