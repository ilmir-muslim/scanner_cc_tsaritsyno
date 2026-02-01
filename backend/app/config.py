from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:password@postgres:5432/qr_system"

    # CORS
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
    DEBUG: bool = False

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
