"""
Media Generator for Nano Banana (Images) & Seedance (Video Animation) with Mock Mode support.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)


class MediaGenerator:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    def generate_image(self, prompt: str, output_path: str) -> str:
        """
        Generates a key scene image or creates a color placeholder in mock mode.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Generating placeholder image for prompt: '{prompt}'")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Create a simple dummy file for mock mode testing
            with open(output_path, "wb") as f:
                f.write(b"MOCK_IMAGE_DATA")
            return output_path
        
        # Real Nano Banana API call implementation will go here
        raise NotImplementedError("Real Nano Banana API call not configured yet.")

    def animate_video(self, image_path: str, prompt: str, output_path: str) -> str:
        """
        Animates an image into a video clip or creates a dummy video file in mock mode.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Animating image {image_path} with Seedance prompt: '{prompt}'")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_VIDEO_DATA")
            return output_path

        # Real Seedance API call implementation will go here
        raise NotImplementedError("Real Seedance API call not configured yet.")
