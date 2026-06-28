import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Existing backend settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 30
    DATABASE_URL: str = "sqlite:///./research_assistant.db"
    LOG_LEVEL: str = "INFO"

    # Gemini settings
    GEMINI_API_KEY: str = ""
    MODEL_NAME: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.2

    # RAG settings
    CONFIDENCE_THRESHOLD: float = 0.20
    MAX_CONTEXT_CHUNKS: int = 5


settings = Settings()