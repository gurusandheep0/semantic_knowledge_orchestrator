from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "PrismRAG API"
    data_dir: Path = ROOT_DIR / "data"
    database_name: str = "prismrag.sqlite3"
    max_file_size_mb: int = 12
    chunk_size: int = 720
    chunk_overlap: int = 110
    embedding_dimensions: int = 128
    retrieval_top_k: int = 4

    use_pinecone: bool = False
    pinecone_api_key: str | None = None
    pinecone_index: str = "prismrag-knowledge"
    pinecone_namespace: str = "workspace"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    telegram_bot_token: str | None = None
    n8n_webhook_secret: str = "replace-this-secret"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / self.database_name


settings = Settings()
