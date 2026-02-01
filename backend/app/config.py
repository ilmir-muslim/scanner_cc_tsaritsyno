import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:password@postgres:5432/qr_system"

    # Определяем среду
    PRODUCTION: bool = os.getenv("PRODUCTION", "false").lower() == "true"

    # CORS настройки в зависимости от среды
    if PRODUCTION:
        ALLOWED_ORIGINS: List[str] = [
            "http://46.23.98.207",
            "http://46.23.98.207:80",
            "http://46.23.98.207:3000",
            "http://46.23.98.207:8003",
            "ws://46.23.98.207",
            "ws://46.23.98.207:80",
            "ws://46.23.98.207:3000",
            "ws://46.23.98.207:8003",
            "https://46.23.98.207",
        ]
    else:
        ALLOWED_ORIGINS: List[str] = [
            "http://localhost:3000",
            "http://frontend:80",
            "http://localhost:8003",
            "ws://localhost:3000",
            "ws://localhost:8003",
        ]

    DEFAULT_PRINTER: Optional[str] = None
    PRINT_AUTO_CONFIRM: bool = True

    APP_NAME: str = "QR Replication System"
    DEBUG: bool = not PRODUCTION

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
