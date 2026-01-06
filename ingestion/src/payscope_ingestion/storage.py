from __future__ import annotations

import boto3

from payscope_ingestion.config import Settings


def build_s3_client(settings: Settings):
    session = boto3.session.Session()
    return session.client(
        "s3",
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
    )


def put_object_file(
    *,
    s3_client,
    bucket: str,
    key: str,
    file_path: str,
    content_type: str | None = None,
) -> None:
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
    with open(file_path, "rb") as f:
        s3_client.upload_fileobj(f, bucket, key, ExtraArgs=extra_args or None)


def delete_object(*, s3_client, bucket: str, key: str) -> None:
    s3_client.delete_object(Bucket=bucket, Key=key)




