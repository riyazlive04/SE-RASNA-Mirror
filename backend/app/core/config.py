from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "SE RASNA Mirror"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./se_rasna_mirror.db"

    AUDIO_STORAGE_PATH: Path = Path("storage/audio")
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_FORMATS: list[str] = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    # LLM Configuration
    OPENAI_API_KEY: str = ""  # Set via environment variable
    LLM_MODEL: str = "gpt-4o-mini"  # Fast, cost-effective model
    LLM_TEMPERATURE: float = 0.0  # Deterministic output
    LLM_MAX_TOKENS: int = 2000  # Reasonable limit for RASNA evaluation
    LLM_TIMEOUT_SECONDS: int = 30  # Timeout for LLM requests
    LLM_MAX_RETRIES: int = 2  # Maximum retry attempts

    # Authentication Configuration
    # CRITICAL: Must be set via environment variable in production
    # Default only for local development (auto-generates secure key)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """
        Validate JWT secret key is properly configured.

        Security: Prevents using weak/default secrets in production.
        For production, JWT_SECRET_KEY MUST be set via environment variable.
        """
        # Check minimum length (32 chars = 256 bits minimum)
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # Warn if it looks like a placeholder (optional, but good practice)
        dangerous_patterns = ["CHANGE", "TODO", "REPLACE", "EXAMPLE", "TEST", "SECRET"]
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError(
                "JWT_SECRET_KEY appears to be a placeholder. "
                "Set a secure random key via environment variable. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        return v

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
