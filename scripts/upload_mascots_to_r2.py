"""
Infrastructure Script: Upload All Mascot Reference Images to Cloudflare R2
Uploads PNG files from assets/mascots/ to Cloudflare R2 bucket 'dookie-tv-assets/mascots/'.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.abspath("."))

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from src.storage.r2_client import CloudflareR2Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("upload_mascots")

sys.stdout.reconfigure(encoding="utf-8")


def upload_mascot_assets():
    mascot_dir = "assets/mascots"
    if not os.path.exists(mascot_dir):
        logger.error(f"Directory '{mascot_dir}' does not exist!")
        return

    # Force real upload mode for R2 storage (0 Segmind API calls)
    r2_client = CloudflareR2Client(mock_mode=False)
    logger.info(f"Connecting to Cloudflare R2 bucket '{r2_client.bucket_name}'...")

    uploaded_files = {}
    for filename in sorted(os.listdir(mascot_dir)):
        if filename.lower().endswith(".png"):
            local_path = os.path.join(mascot_dir, filename)
            destination_key = f"mascots/{filename}"
            
            logger.info(f"Uploading '{filename}' to R2 key '{destination_key}'...")
            try:
                public_url = r2_client.upload_file(local_path=local_path, destination_key=destination_key)
                uploaded_files[filename] = public_url
                logger.info(f"✅ Uploaded '{filename}': {public_url}")
            except Exception as e:
                logger.error(f"❌ Failed to upload '{filename}': {e}")

    print("\n--- R2 Upload Summary ---")
    for fname, url in uploaded_files.items():
        print(f"{fname} -> {url}")


if __name__ == "__main__":
    upload_mascot_assets()
