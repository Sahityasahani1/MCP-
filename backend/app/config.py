"""Backend Configuration and Settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous ML Research Agent"
    VERSION: str = "2.0.0"
    
    # Model Provider Selection
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "gemini")
    
    # Provider Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "processed_data"

    # Security & Authentication
    API_AUTH_KEY: str = os.getenv("API_AUTH_KEY", "amra-secret-key-2026")
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "true").lower() in ("true", "1", "yes")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "amra-jwt-production-secret-key-2026-v2")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7

    # OAuth 2.0 Identity Providers
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:3000")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")

    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
