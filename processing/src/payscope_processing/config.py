from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    service_name: str = "processing"
    database_dsn: str  # asyncpg DSN, e.g. postgresql://user:pass@host:5432/db

    celery_broker_url: str

    # Object storage (S3/MinIO)
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket: str = "payscope-raw"

    # Model/cache
    hf_home: str | None = None

    # LLM mapping (OpenAI-compatible)
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_s: float = 30.0
    mapping_confidence_threshold: float = 0.70
    
    # Free LLM options (for LLaMA integration)
    llm_provider: str = "openai"  # "openai", "hf", "local", "auto"
    hf_api_token: str | None = None
    llm_local_provider: str = "ollama"  # "ollama" or "vllm"
    llm_local_base_url: str | None = None
    llm_local_model: str | None = None

    # Embeddings
    embedding_model_name: str = "BAAI/bge-base-en-v1.5"
    embedding_device: str | None = None

    # Pinecone
    pinecone_api_key: str | None = None
    pinecone_index_name: str | None = None
    pinecone_namespace: str = "payscope"

    # Neo4j
    neo4j_uri: str | None = None
    neo4j_user: str | None = None
    neo4j_password: str | None = None

    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


