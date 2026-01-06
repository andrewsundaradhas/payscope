from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Service identity
    service_name: str = "ingestion"

    # Database
    database_url: str

    # Object storage (S3/MinIO)
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket: str = "payscope-raw"

    # Celery broker (used to enqueue jobs after upload)
    celery_broker_url: str

    # Logging
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]




