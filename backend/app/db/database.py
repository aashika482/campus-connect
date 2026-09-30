from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# libpq-style options Neon puts in its URLs that asyncpg rejects (SSL is set via connect_args)
_UNSUPPORTED_PARAMS = {"sslmode", "channel_binding"}


def _make_async_url(url: str) -> str:
    """Point the URL at the asyncpg driver and drop query params asyncpg doesn't accept."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(query)))


engine = create_async_engine(
    _make_async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    # Neon closes idle connections (and suspends the database after ~5 min idle).
    # Without this, the first request after a quiet period got a dead pooled
    # connection and failed with a 500 ("connection is closed"). pre_ping checks
    # each connection before handing it out and transparently replaces dead ones.
    pool_pre_ping=True,
    connect_args={"ssl": True},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


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
