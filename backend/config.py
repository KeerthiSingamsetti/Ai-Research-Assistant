import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 30
    DATABASE_URL: str = "sqlite:///./research_assistant.db"
    LOG_LEVEL: str = "INFO"

# Instantiate settings
settings = Settings()
