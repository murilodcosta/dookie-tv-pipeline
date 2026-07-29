"""
Pipeline Steps 3.2 & 3.3: Media Generator using Fixed Mascot Assets & Segmind Seedance 2.0 API.
Note: Fixed mascot images are stored in assets/mascots/ and animated into clips using Segmind Seedance 2.0.
"""

import os
import base64
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

SEGMIND_SEEDANCE_URL = "https://api.segmind.com/v1/seedance-2.0"


class MediaGenerator:
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key or os.getenv("SEGMIND_API_KEY")
        self.mock_mode = mock_mode

    def get_mascot_asset(self, mascot: str) -> str:
        """
        Retrieves the fixed pre-generated mascot reference asset path from assets/mascots/.
        """
        mascot_clean = mascot.lower().strip()
        candidates = [
            f"assets/mascots/{mascot_clean}-character.png",
            f"assets/mascots/{mascot_clean}.png",
            f"assets/{mascot_clean}-character.png",
            f"assets/{mascot_clean}.png",
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                logger.info(f"Using mascot reference asset: '{candidate}'")
                return candidate
        
        fallback_path = candidates[0]
        logger.warning(f"Mascot asset not found for '{mascot}'. Defaulting to '{fallback_path}'")
        return fallback_path

    def animate_video(self, image_path: str, prompt: str, output_path: str, force_recreate: bool = False) -> str:
        """
        Animates a mascot reference image into a 9:16 vertical video clip via Segmind Seedance 2.0.
        Includes local caching (re-uses existing video if downstream step fails to avoid wasting API credits).
        Enforces 3D Pixar animated cartoon style to prevent realistic animal output.
        """
        # LOCAL CACHE CHECK: Never spend credits to re-generate if valid video file exists on disk!
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100000 and not force_recreate:
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"🛡️ [CACHE HIT] Existing generated video found at '{output_path}' ({file_size_mb:.2f} MB). Re-using file & skipping Segmind API call to save credits!")
            return output_path

        if self.mock_mode or not self.api_key:
            logger.info(f"[MOCK] Animating asset {image_path} with Seedance prompt: '{prompt[:40]}...'")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_SEGMIND_SEEDANCE_VIDEO_DATA")
            return output_path

        logger.info(f"Connecting to Segmind Seedance 2.0 API for animation (Full HD 1080p)...")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        
        # Prepare image input: convert local file to data URI / base64 if needed
        image_input = image_path
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode("utf-8")
                image_input = f"data:image/png;base64,{b64_data}"

        # Enforce 3D Pixar Animated Cartoon style prefix so Seedance never outputs realistic animals!
        styled_prompt = (
            "3D Pixar animated cartoon style, stylized cute 3D mascot character identical to reference image, "
            "bright vibrant children's animation, smooth 3D render, NOT realistic photo, NO real live-action animals. "
            f"{prompt}"
        )

        # Segmind Seedance 2.0 payload parameters
        payload = {
            "prompt": styled_prompt,
            "image": image_input,
            "aspect_ratio": "9:16",
            "duration": 10,
            "generate_audio": False,
        }

        try:
            # Set 300s (5 min) timeout for video rendering on Segmind servers
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
