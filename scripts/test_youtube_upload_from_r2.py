"""
Test script to download the last real video from Cloudflare R2
and publish it to YouTube Shorts using OAuth2 (privacyStatus="unlisted").
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.upload.youtube_uploader import YouTubeUploader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

R2_VIDEO_URL = "https://pub-e726103cf37145cd8aa562e81d9193d2.r2.dev/shorts/2026-07-30_dookie_numbers_1_to_10.mp4"
LOCAL_TEST_VIDEO_PATH = os.path.abspath("data/output/temp/test_r2_short.mp4")


def main():
    logger.info("🧪 Starting YouTube Shorts Upload Test from Cloudflare R2...")

    # 1. Download last real video from Cloudflare R2
    os.makedirs(os.path.dirname(LOCAL_TEST_VIDEO_PATH), exist_ok=True)
    logger.info(f"Downloading video from Cloudflare R2: {R2_VIDEO_URL}...")
    response = requests.get(R2_VIDEO_URL, timeout=60)
    response.raise_for_status()

    with open(LOCAL_TEST_VIDEO_PATH, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded video ({len(response.content)} bytes) to '{LOCAL_TEST_VIDEO_PATH}'.")

    # 2. Publish to YouTube Shorts (mock_mode=False)
    uploader = YouTubeUploader(mock_mode=False)
    
    title = "Dookie Learns Numbers 1 to 10! 🎨 #learning #numbers"
    description = "Join Dookie on Dookie Tv as we learn about numbers 1 to 10! #numbers_1_to_10 #learning #kids #shorts #dookietv"
    tags = ["kids", "shorts", "learning", "numbers_1_to_10", "dookietv"]

    youtube_url = uploader.upload_short(
        video_path=LOCAL_TEST_VIDEO_PATH,
        title=title,
        description=description,
        tags=tags,
        privacy_status="unlisted",
    )

    print("\n" + "=" * 80)
    print("🚀 YOUTUBE SHORTS UPLOAD SUCCESSFUL!")
    print(f"🔗 Published YouTube Short URL: {youtube_url}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
