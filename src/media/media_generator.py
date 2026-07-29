"""
Pipeline Steps 3.2 & 3.3: Media Generator using Fixed Mascot Assets & Segmind Seedance 2.0 API.
Note: Fixed mascot reference images are uploaded to Cloudflare R2 and passed via reference_images array to Segmind.
"""

import os
import logging
import requests
from typing import Optional, List
from src.storage.r2_client import CloudflareR2Client

logger = logging.getLogger(__name__)

SEGMIND_SEEDANCE_URL = "https://api.segmind.com/v1/seedance-2.0"


class MediaGenerator:
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key or os.getenv("SEGMIND_API_KEY")
        self.mock_mode = mock_mode
        self.r2_client = CloudflareR2Client(mock_mode=mock_mode)

    def get_mascot_reference_urls(self, mascot: str) -> List[str]:
        """
        Ensures mascot character and character-sheets PNG images are uploaded to R2 and returns their public URLs.
        Segmind Seedance 2.0 expects array of reference image URLs in payload parameter 'reference_images'.
        """
        mascot_clean = mascot.lower().strip()
        local_char = f"assets/mascots/{mascot_clean}-character.png"
        local_sheet = f"assets/mascots/{mascot_clean}-character-sheets.png"

        # Account ID for Cloudflare R2 public / endpoint URL format
        account_id = os.getenv("R2_ACCOUNT_ID", "62200b61d954c569c2a0b1b147f08397")
        bucket_name = os.getenv("R2_BUCKET_NAME", "dookie-tv-assets")

        urls = []
        for key, local_file in [("character.png", local_char), ("character-sheets.png", local_sheet)]:
            r2_dest_key = f"mascots/{mascot_clean}-{key}"
            if os.path.exists(local_file) and not self.mock_mode:
                try:
                    uploaded_url = self.r2_client.upload_file(local_file, r2_dest_key)
                    urls.append(uploaded_url)
                except Exception as err:
                    logger.warning(f"Failed to upload {local_file} to R2: {err}")
                    fallback_url = f"https://{account_id}.r2.cloudflarestorage.com/{bucket_name}/{r2_dest_key}"
                    urls.append(fallback_url)
            else:
                fallback_url = f"https://{account_id}.r2.cloudflarestorage.com/{bucket_name}/{r2_dest_key}"
                urls.append(fallback_url)

        logger.info(f"Mascot '{mascot}' reference URLs for Segmind Seedance 2.0: {urls}")
        return urls

    def get_mascot_asset(self, mascot: str) -> str:
        """
        Retrieves the fixed pre-generated mascot reference asset path locally.
        """
        mascot_clean = mascot.lower().strip()
        candidates = [
            f"assets/mascots/{mascot_clean}-character.png",
            f"assets/mascots/{mascot_clean}.png",
            f"assets/{mascot_clean}-character.png",
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        return candidates[0]

    def animate_video(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        mascot: str = "dookie",
        force_recreate: bool = False,
    ) -> str:
        """
        Animates mascot reference images into a 9:16 vertical video clip via Segmind Seedance 2.0.
        Uses exact 'reference_images' array payload structure with public R2 image URLs.
        Includes local caching (re-uses existing video if file exists on disk).
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

        logger.info(f"Connecting to Segmind Seedance 2.0 API for mascot '{mascot}' (Full HD 1080p)...")
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Retrieve public R2 URLs for reference_images array
        ref_image_urls = self.get_mascot_reference_urls(mascot)

        # Enforce image reference in prompt text so Seedance binds character visual identity from image 1 and image 2!
        if "image 1" not in prompt.lower():
            styled_prompt = (
                f"{mascot.capitalize()}, the mascot character from image 1 and image 2, "
                "is in 3D Pixar animated cartoon style, stylized cute 3D character, smooth 3D render, NOT realistic photo, NO real live-action animals. "
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
        }

        try:
            logger.info(f"Sending Segmind Seedance 2.0 Payload with reference_images: {ref_image_urls}")
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
