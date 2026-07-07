import uuid

import boto3
from botocore.client import Config as BotoConfig

from app.config import settings

_s3_kwargs = {
    "aws_access_key_id": settings.S3_ACCESS_KEY,
    "aws_secret_access_key": settings.S3_SECRET_KEY,
    "region_name": settings.S3_REGION,
    "config": BotoConfig(signature_version="s3v4"),
}
if settings.S3_ENDPOINT_URL:
    # Supabase storage / MinIO / any S3-compatible endpoint
    _s3_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

s3_client = boto3.client("s3", **_s3_kwargs)


def build_object_key(booking_id: uuid.UUID, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    return f"reports/{booking_id}/{uuid.uuid4()}.{ext}"


def upload_file(file_bytes: bytes, key: str, content_type: str = "application/pdf") -> None:
    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )


def generate_signed_url(key: str) -> str:
    """Generates a time-limited signed URL so reports aren't publicly readable —
    ownership is checked in the router before this is ever called."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.SIGNED_URL_EXPIRY_SECONDS,
    )


def download_file(key: str) -> bytes:
    """Fetches the raw uploaded report back out of storage - used by the OCR
    extraction pipeline, which needs the actual file bytes, not a signed URL."""
    response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    return response["Body"].read()
