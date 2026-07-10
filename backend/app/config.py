"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_env: str = "development"
    secret_key: str = "change-me"
    token_encryption_key: str = ""

    # Single-user local auth
    admin_username: str = "admin"
    admin_password: str = "change-me"

    # Datastores
    database_url: str = "postgresql+psycopg://autotube:autotube@postgres:5432/autotube"
    redis_url: str = "redis://redis:6379/0"

    # Object storage
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "autotube-media"
    s3_region: str = "us-east-1"

    # AI providers
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    pexels_api_key: str = ""

    # Vertex / Veo
    vertex_project_id: str = ""
    vertex_location: str = "us-central1"
    veo_enabled: bool = False

    # Additional AI-video providers (pluggable hero clips)
    video_provider: str = "veo"  # veo | runway | luma | kling | none
    runway_api_key: str = ""
    luma_api_key: str = ""
    kling_access_key: str = ""
    kling_secret_key: str = ""

    # Whisper
    whisper_model: str = "base"
    whisper_device: str = "cpu"

    # YouTube OAuth
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8000/api/auth/youtube/callback"

    # Web app URL (for post-OAuth redirect)
    web_app_url: str = "http://localhost:5173"

    # Cost guardrails (USD). 0 disables a cap.
    cost_cap_per_video_usd: float = 2.00
    cost_cap_per_channel_daily_usd: float = 10.00
    cost_cap_global_daily_usd: float = 50.00


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
