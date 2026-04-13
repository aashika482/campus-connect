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
    # Comma-separated list of allowed frontend URLs for production
    # e.g. https://campulse.vercel.app,https://campulse-git-main-user.vercel.app
    FRONTEND_URLS: str = ""

    @property
    def all_cors_origins(self) -> List[str]:
        origins = list(self.CORS_ORIGINS)
        for url in self.FRONTEND_URLS.split(","):
            url = url.strip().rstrip("/")
            if url:
                origins.append(url)
        return origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
