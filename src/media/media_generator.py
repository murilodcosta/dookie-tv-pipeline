"""
Pipeline Steps 3.2 & 3.3: Media Generator using Fixed Mascot Assets & Segmind Seedance 2.0 API.
Note: Fixed mascot images are stored in assets/mascots/ and animated into clips using Segmind Seedance 2.0.
"""

import os
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
        asset_path = f"assets/mascots/{mascot_clean}.png"
        
        # Fallback check
        if not os.path.exists(asset_path):
            alt_path = f"assets/{mascot_clean}-character.png"
            if os.path.exists(alt_path):
                return alt_path
        
        logger.info(f"Using mascot reference asset: '{asset_path}'")
        return asset_path

    def animate_video(self, image_path: str, prompt: str, output_path: str) -> str:
        """
        Animates a mascot reference image into a 9:16 vertical video clip via Segmind Seedance 2.0.
        """
        if self.mock_mode or not self.api_key:
            logger.info(f"[MOCK] Animating asset {image_path} with Seedance prompt: '{prompt[:40]}...'")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_SEGMIND_SEEDANCE_VIDEO_DATA")
            return output_path

        logger.info(f"Connecting to Segmind Seedance 2.0 API for animation...")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        
        # Segmind Seedance 2.0 payload parameters
        payload = {
            "prompt": prompt,
            "image": image_path,  # URL or base64
            "aspect_ratio": "9:16",
            "duration": 5,
            "generate_audio": False,
        }

        try:
            response = requests.post(SEGMIND_SEEDANCE_URL, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            # Save output binary video stream
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Successfully rendered video clip: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error calling Segmind Seedance 2.0 API: {e}")
            raise e
