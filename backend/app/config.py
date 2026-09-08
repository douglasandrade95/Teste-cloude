import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "AutoVideoEditor"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/auto_video_editor"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI/ML APIs
    # These are fallbacks only: keys saved through the Integrações screen live
    # in the encrypted vault and take priority over anything set here.
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    replicate_api_token: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Credential vault (see app/services/vault.py)
    ave_vault_dir: str = "~/.autovideoeditor"
    ave_master_key: str = ""  # optional: pin the encryption key via env
    ave_admin_token: str = ""  # optional: required to edit settings remotely

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "auto-video-editor-uploads"
    aws_region: str = "us-east-1"
    use_s3: bool = False

    # File Upload
    max_file_size: int = 5368709120  # 5GB in bytes
    max_video_duration: int = 600  # 10 minutes
    upload_directory: str = "/tmp/uploads"
    supported_formats: list = ["mp4", "mov", "avi", "mkv"]

    # Processing
    ffmpeg_timeout: int = 3600
    processing_queue_name: str = "video_processing"
    worker_concurrency: int = 2

    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
