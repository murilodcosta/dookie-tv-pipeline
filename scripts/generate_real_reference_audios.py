"""
Generate valid 10-second reference MP3 files (vocal_reference.mp3 and music_reference.mp3)
and upload them to Cloudflare R2 bucket dookie-tv-assets/audio/
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.storage.r2_client import CloudflareR2Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_audios():
    import edge_tts

    audio_dir = os.path.abspath("assets/audio")
    os.makedirs(audio_dir, exist_ok=True)

    vocal_path = os.path.join(audio_dir, "vocal_reference.mp3")
    music_path = os.path.join(audio_dir, "music_reference.mp3")

    logger.info("Generating real 10s vocal reference audio using Edge-TTS en-US-AnaNeural...")
    vocal_text = "Welcome to Dookie TV! Let's learn together and have fun!"
    comm_vocal = edge_tts.Communicate(text=vocal_text, voice="en-US-AnaNeural")
    await comm_vocal.save(vocal_path)
    logger.info(f"Saved real vocal reference audio ({os.path.getsize(vocal_path)} bytes): {vocal_path}")

    logger.info("Generating real 10s music reference audio using Edge-TTS en-US-SteffanNeural...")
    music_text = "La la la cheerful happy background music playing brightly for kids!"
    comm_music = edge_tts.Communicate(text=music_text, voice="en-US-SteffanNeural")
    await comm_music.save(music_path)
    logger.info(f"Saved real music reference audio ({os.path.getsize(music_path)} bytes): {music_path}")

    # Upload both valid MP3 files to R2
    r2_client = CloudflareR2Client(mock_mode=False)
    for filename in ["vocal_reference.mp3", "music_reference.mp3"]:
        local_path = os.path.join(audio_dir, filename)
        dest_key = f"audio/{filename}"
        public_url = r2_client.upload_file(local_path=local_path, destination_key=dest_key)
        logger.info(f"✅ Uploaded valid MP3 '{filename}' to R2 -> {public_url}")


if __name__ == "__main__":
    asyncio.run(generate_audios())
