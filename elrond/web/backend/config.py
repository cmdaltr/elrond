"""
Web Backend Configuration

Configuration settings for the elrond web interface backend.
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "elrond Web Interface"
    app_version: str = "2.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Storage
    upload_dir: Path = Path("/tmp/elrond/uploads")
    output_dir: Path = Path("/tmp/elrond/output")
    max_upload_size: int = 100 * 1024 * 1024 * 1024  # 100GB

    # Session
    secret_key: str = "your-secret-key-change-in-production"
    session_timeout: int = 3600  # 1 hour

    # Analysis
    max_concurrent_analyses: int = 3
    analysis_timeout: int = 86400  # 24 hours

    # Paths - allowed directories for file browsing
    allowed_paths: list = ["/mnt", "/media", "/tmp/elrond"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Create necessary directories
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
