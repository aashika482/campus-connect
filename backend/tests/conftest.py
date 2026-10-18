# Test setup: a real Postgres, migrated with Alembic, wiped before every test.
#
#   cd backend
#   pip install -r requirements-dev.txt
#   pytest
#
# With TEST_DATABASE_URL set (e.g. in CI) that database is used, and it gets wiped.
# Without it, a throwaway Postgres is started in a temp folder (pgserver) and deleted after.

import os
import tempfile

import pytest

if not os.environ.get("TEST_DATABASE_URL"):
    import pgserver
    _server = pgserver.get_server(tempfile.mkdtemp(prefix="campulse-test-"), cleanup_mode="delete")
    _server.psql("CREATE DATABASE campulse_test;")
    os.environ["TEST_DATABASE_URL"] = _server.get_uri("campulse_test")
    os.environ["DATABASE_SSL"] = "false"
# The app reads its settings at import time, so point it at the test database first
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ["STUDENT_EMAIL_DOMAINS"] = "muj.manipal.edu"
os.environ["FACULTY_EMAIL_DOMAINS"] = "jaipur.manipal.edu"
os.environ["MAX_EDITORS_PER_CLUB"] = "1"   # small, so the limit is easy to hit

import httpx  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

from main import app  # noqa: E402
from app.db.database import engine  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLUBS = [(1, "IEEE Computer Society", "IEEE"), (2, "ACM Student Chapter", "ACM")]
PASSWORD = "secret123"


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    """Build the schema exactly as production does: through the Alembic migrations."""
    command.upgrade(Config(os.path.join(BACKEND, "alembic.ini")), "head")


@pytest.fixture(autouse=True)
async def clean_db():
    """Every test starts with the two clubs and nothing else."""
    async with engine.begin() as conn:
        tables = (await conn.execute(text(
            "SELECT string_agg(tablename, ', ') FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        ))).scalar()
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        for id_, name, abbr in CLUBS:
            await conn.execute(text(
                "INSERT INTO clubs (id, name, abbr, description, color, tags, member_count, is_open) "
                "VALUES (:id, :name, :abbr, 'd', '#000', 'tech', 0, true)"), {"id": id_, "name": name, "abbr": abbr})
    yield


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def set_account_type(email: str, account_type: str) -> None:
    """Make dsw / platform_admin accounts directly (the app only lets admins do this)."""
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE users SET account_type = :t WHERE email = :e"), {"t": account_type, "e": email})


@pytest.fixture
def signup(client):
    """signup("asha@muj.manipal.edu") -> auth headers for a new account (optionally retyped)."""
    async def _signup(email: str, account_type: str | None = None) -> dict:
        r = await client.post("/api/auth/register", json={
            "name": email.split("@")[0].title(), "email": email, "password": PASSWORD, "phone": "9876543210",
        })
        assert r.status_code == 201, r.text
        if account_type:
            await set_account_type(email, account_type)
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _signup
