from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@mysql:3306/qr_system"

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://frontend:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # Printer settings
    DEFAULT_PRINTER: Optional[str] = None
    PRINT_AUTO_CONFIRM: bool = True

    # Application settings
    APP_NAME: str = "QR Replication System"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
