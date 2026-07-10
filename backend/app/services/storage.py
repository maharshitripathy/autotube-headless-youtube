"""S3/MinIO object storage helper."""
from __future__ import annotations

import io

import boto3
from botocore.client import Config

from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
    return _client


def ensure_bucket() -> None:
    client = _get_client()
    existing = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in existing:
        client.create_bucket(Bucket=settings.s3_bucket)


def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_bucket()
    _get_client().put_object(
        Bucket=settings.s3_bucket, Key=key, Body=io.BytesIO(data), ContentType=content_type
    )
    return key


def download_bytes(key: str) -> bytes:
    obj = _get_client().get_object(Bucket=settings.s3_bucket, Key=key)
    return obj["Body"].read()


def presigned_url(key: str, expires: int = 3600) -> str:
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires,
    )
