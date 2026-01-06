from __future__ import annotations

import boto3

from payscope_processing.config import Settings


def build_s3_client(settings: Settings):
    session = boto3.session.Session()
    return session.client(
        "s3",
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
    )


def download_to_file(*, s3_client, bucket: str, key: str, file_path: str) -> None:
    with open(file_path, "wb") as f:
        s3_client.download_fileobj(bucket, key, f)


def upload_json_bytes(*, s3_client, bucket: str, key: str, data: bytes) -> None:
    s3_client.put_object(Bucket=bucket, Key=key, Body=data, ContentType="application/json")




