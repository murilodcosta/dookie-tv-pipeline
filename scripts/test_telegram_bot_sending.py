"""
Test script to verify real Telegram Bot API sending to personal Telegram chat.
Sends video preview with interactive inline buttons (Approve, Reject, Redo).
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.upload.telegram_bot import TelegramApprovalGateway

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

R2_VIDEO_URL = "https://pub-e726103cf37145cd8aa562e81d9193d2.r2.dev/shorts/2026-07-30_dookie_numbers_1_to_10.mp4"
LOCAL_TEST_VIDEO_PATH = os.path.abspath("data/output/temp/test_r2_short.mp4")


def main():
    logger.info("🧪 Starting Real Telegram Bot Sending Test...")

    # 1. Ensure test video exists
    if not os.path.exists(LOCAL_TEST_VIDEO_PATH):
        logger.info(f"Downloading video from Cloudflare R2: {R2_VIDEO_URL}...")
        response = requests.get(R2_VIDEO_URL, timeout=60)
        response.raise_for_status()
        os.makedirs(os.path.dirname(LOCAL_TEST_VIDEO_PATH), exist_ok=True)
        with open(LOCAL_TEST_VIDEO_PATH, "wb") as f:
            f.write(response.content)

    # 2. Instantiate TelegramApprovalGateway in real mode (mock_mode=False)
    telegram = TelegramApprovalGateway(mock_mode=False)

    title = "Dookie Learns Numbers 1 to 10! 🎨 #learning #numbers"
    description = (
        "Join Dookie on Dookie Tv as we learn about numbers 1 to 10! 🐶\n\n"
        "New videos coming soon from Dookie Tv — stay tuned for more with Dookie, Mia, and Carrot! 🎨\n\n"
        "#numbers_1_to_10 #learning #kids #shorts #dookietv"
    )

    logger.info("Sending video preview with interactive buttons to your Telegram chat...")
    telegram.send_video_for_review(
        video_path=LOCAL_TEST_VIDEO_PATH,
        title=title,
        description=description,
        cost=0.8502,
        mascot="dookie",
        topic="numbers_1_to_10",
    )

    print("\n" + "=" * 80)
    print("📲 TELEGRAM MESSAGE SENT! Check your Telegram app on your phone.")
    print("Aguardando seu clique no botão no Telegram (timeout: 120s)...")
    print("=" * 80 + "\n")

    decision = telegram.wait_for_user_decision(timeout_seconds=120)
    
    print("\n" + "=" * 80)
    print(f"🎉 DECISÃO RECEBIDA DO TELEGRAM: '{decision.upper()}'")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
