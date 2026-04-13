from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CamPulse"
    DEBUG: bool = False

    # Database — paste your Neon connection string here
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — add your deployed frontend URL here in production
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    FRONTEND_URL: str = ""  # e.g. https://campulse.vercel.app

    @property
    def all_cors_origins(self) -> List[str]:
        origins = list(self.CORS_ORIGINS)
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.rstrip("/"))
        return origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
