"""
Cloudflare R2 Object Storage client with S3 API compatibility via boto3 and local fallback.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CloudflareR2Client:
    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: str = "dookie-tv-media",
        mock_mode: bool = True,
    ):
        self.account_id = account_id or os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("R2_BUCKET_NAME", "dookie-tv-media")
        self.mock_mode = mock_mode

    def upload_file(self, local_path: str, destination_key: str) -> str:
        """
        Uploads a local media file to the Cloudflare R2 bucket or logs in mock mode.
        """
        if self.mock_mode or not (self.account_id and self.access_key_id and self.secret_access_key):
            logger.info(
                f"[MOCK] R2 Client: Uploaded {local_path} to Cloudflare R2 bucket '{self.bucket_name}' key '{destination_key}'."
            )
            return f"https://mock-r2.cloudflarestorage.com/{self.bucket_name}/{destination_key}"

        try:
            import boto3

            endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
            s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
            )
            s3_client.upload_file(local_path, self.bucket_name, destination_key)
            logger.info(f"Successfully uploaded {local_path} to R2 bucket '{self.bucket_name}'.")
            return f"{endpoint_url}/{self.bucket_name}/{destination_key}"
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to Cloudflare R2: {e}")
            raise
