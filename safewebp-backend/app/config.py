# app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SafeWebp API"
    UPLOAD_DIR: Path = Path("static/uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
    
    class Config:
        env_file = ".env"

settings = Settings()

# Klasörleri oluştur
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)