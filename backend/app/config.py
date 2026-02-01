import os
from typing import List


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://user:password@postgres:5432/qr_system"
    )
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self.DEBUG:
            return [
                "http://localhost:3000",
                "http://frontend:80",
                "http://localhost:8003",
                "ws://localhost:3000",
                "ws://localhost:8003",
            ]
        else:
            return [
                "http://46.23.98.207",
                "https://46.23.98.207",
                "ws://46.23.98.207",
                "wss://46.23.98.207",
            ]


settings = Settings()
