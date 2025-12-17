from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "SE RASNA Mirror"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./se_rasna_mirror.db"

    AUDIO_STORAGE_PATH: Path = Path("storage/audio")
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_FORMATS: list[str] = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    class Config:
        case_sensitive = True


settings = Settings()
