from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal


def _csv(value: str) -> List[str]:
    """Comma-separated env value -> list (pydantic-settings would expect JSON for List[str])."""
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CamPulse"
    DEBUG: bool = False

    # Database — paste your Neon connection string here
    DATABASE_URL: str
    # Neon requires SSL. Set False only for a local Postgres (dev / tests).
    DATABASE_SSL: bool = True

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

    # College email domains (comma-separated, no "@"). The domain decides a new account's
    # type; anything else can't sign up.
    STUDENT_EMAIL_DOMAINS: str = "muj.manipal.edu"
    FACULTY_EMAIL_DOMAINS: str = "jaipur.manipal.edu"

    # Most active editors one club can have (it has exactly one owner). The DSW can't
    # approve past this, so a club's team stays small and accountable.
    MAX_EDITORS_PER_CLUB: int = 5

    # Demo data (python -m app.db.demo). Refuses to run unless DEMO_MODE is true, so it can
    # never wipe a production database. Every demo account gets DEMO_PASSWORD.
    DEMO_MODE: bool = False
    DEMO_PASSWORD: str = ""

    # Cloudinary (signed poster uploads). All three come from the Cloudinary
    # dashboard. The secret stays on the server; if any is missing, uploads are
    # disabled and the poster field falls back to pasting an image URL.
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    @property
    def cors_origins(self) -> List[str]:
        # Browsers send the origin without a trailing slash, so strip it to match
        return [o.rstrip("/") for o in _csv(self.CORS_ORIGINS)]

    @property
    def email_domains(self) -> dict[str, List[str]]:
        return {"student": _csv(self.STUDENT_EMAIL_DOMAINS), "faculty": _csv(self.FACULTY_EMAIL_DOMAINS)}

    def account_kind_for(self, email: str) -> Literal["student", "faculty"] | None:
        """Which kind of college account this email may create, or None if its domain isn't allowed."""
        domain = email.rsplit("@", 1)[-1].lower()
        return next((kind for kind, domains in self.email_domains.items() if domain in domains), None)

    @property
    def cloudinary_enabled(self) -> bool:
        return bool(self.CLOUDINARY_CLOUD_NAME and self.CLOUDINARY_API_KEY and self.CLOUDINARY_API_SECRET)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
