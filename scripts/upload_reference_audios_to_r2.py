"""
Helper script to upload fixed audio reference tracks (vocal_reference.mp3 and music_reference.mp3)
from assets/audio/ to Cloudflare R2 bucket dookie-tv-assets/audio/
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.storage.r2_client import CloudflareR2Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    r2_client = CloudflareR2Client(mock_mode=False)
    audio_dir = os.path.abspath("assets/audio")

    # Create dummy reference files if they don't exist locally
    vocal_path = os.path.join(audio_dir, "vocal_reference.mp3")
    music_path = os.path.join(audio_dir, "music_reference.mp3")

    if not os.path.exists(vocal_path):
        with open(vocal_path, "wb") as f:
            f.write(b"MOCK_VOCAL_REFERENCE_AUDIO_BYTES")
        logger.info(f"Created initial vocal reference file at {vocal_path}")

    if not os.path.exists(music_path):
        with open(music_path, "wb") as f:
            f.write(b"MOCK_MUSIC_REFERENCE_AUDIO_BYTES")
        logger.info(f"Created initial music reference file at {music_path}")

    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]
    logger.info(f"Found {len(audio_files)} reference audio files to upload to Cloudflare R2...")

    for filename in audio_files:
        local_file_path = os.path.join(audio_dir, filename)
        destination_key = f"audio/{filename}"
        public_url = r2_client.upload_file(local_path=local_file_path, destination_key=destination_key)
        logger.info(f"✅ Uploaded '{filename}' -> Public URL: {public_url}")


if __name__ == "__main__":
    main()
