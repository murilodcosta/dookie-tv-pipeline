"""
Cloudflare R2 Object Storage client with S3 API compatibility via boto3 and presigned public URL support.
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
        bucket_name: Optional[str] = None,
        mock_mode: bool = True,
    ):
        self.account_id = account_id or os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("R2_BUCKET_NAME") or "dookie-tv-assets"
        self.public_domain = os.getenv("R2_PUBLIC_DOMAIN", "").strip().rstrip("/")
        self.mock_mode = mock_mode

    def get_public_url(self, destination_key: str, expires_in: int = 604800) -> str:
        """
        Generates a public URL for an object in Cloudflare R2:
        - If R2_PUBLIC_DOMAIN is configured (e.g. pub-xxx.r2.dev), uses that domain.
        - Otherwise generates an S3 presigned URL valid for up to 7 days (604,800 seconds), accessible by Segmind/browsers.
        """
        if self.mock_mode or not (self.account_id and self.access_key_id and self.secret_access_key):
            return f"https://mock-r2.cloudflarestorage.com/{self.bucket_name}/{destination_key}"

        if self.public_domain:
            domain_url = self.public_domain if self.public_domain.startswith("http") else f"https://{self.public_domain}"
            return f"{domain_url}/{destination_key}"

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
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": destination_key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL for {destination_key}: {e}")
            return f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket_name}/{destination_key}"

    def upload_file(self, local_path: str, destination_key: str) -> str:
        """
        Uploads a local media file to the Cloudflare R2 bucket and returns its public URL.
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

            return self.get_public_url(destination_key)
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to Cloudflare R2: {e}")
            raise
