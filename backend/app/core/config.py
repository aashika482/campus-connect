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

    # CORS — comma-separated frontend origins allowed to call the API.
    # The default is for local dev; in production set it to the deployed frontend,
    # e.g. CORS_ORIGINS=https://campulse.vercel.app
    # (A plain string, not List[str]: pydantic-settings would expect JSON for a list.)
    CORS_ORIGINS: str = "http://localhost:5173"

    # Cloudinary (signed poster uploads). All three come from the Cloudinary
    # dashboard. The secret stays on the server; if any is missing, uploads are
    # disabled and the poster field falls back to pasting an image URL.
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    @property
    def cors_origins(self) -> List[str]:
        # Browsers send the origin without a trailing slash, so strip it to match
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cloudinary_enabled(self) -> bool:
        return bool(self.CLOUDINARY_CLOUD_NAME and self.CLOUDINARY_API_KEY and self.CLOUDINARY_API_SECRET)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
