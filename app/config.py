from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = "redis://localhost:6379/0"
    standards_path: str = "standards/enduro_standard.json"
    upload_dir: str = "/tmp/uploads"
    max_video_size_mb: int = 50
    mediapipe_model_complexity: int = 1


settings = Settings()
