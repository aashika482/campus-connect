"""Alembic environment: how `alembic upgrade/downgrade/revision` connect to the database.

It reuses the app's own settings, so migrations always hit the same database as the app
(DATABASE_URL from backend/.env, same URL clean-up and SSL). Base.metadata, filled by
importing app.models, is what `--autogenerate` compares the live database against.
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import settings
from app.db.database import Base, _make_async_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
DATABASE_URL = _make_async_url(settings.DATABASE_URL)

# Also compare column types and server defaults, so autogenerate notices e.g. String(50) -> String(100)
COMPARE_OPTIONS = dict(compare_type=True, compare_server_default=True)


def run_migrations_offline() -> None:
    """`alembic upgrade head --sql`: print the SQL instead of running it (for review)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **COMPARE_OPTIONS,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, **COMPARE_OPTIONS)
    with context.begin_transaction():   # each run is one transaction: all migrations apply, or none
        context.run_migrations()


async def run_async_migrations() -> None:
    # NullPool: a one-off command, no need to keep connections around
    engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool, connect_args={"ssl": True})
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
