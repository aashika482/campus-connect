# backend/app/db/database.py
# REPLACE your existing file with this (only change: added discussion import)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _make_async_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    for param in ("sslmode", "channel_binding"):
        import re
        url = re.sub(rf"[?&]{param}=[^&]*", "", url)
    url = url.rstrip("?&")
    return url


engine = create_async_engine(
    _make_async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": True},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    """Create all tables on startup (dev-friendly)."""
    from app.models import user, club, event, membership, discussion  # ← added discussion
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
