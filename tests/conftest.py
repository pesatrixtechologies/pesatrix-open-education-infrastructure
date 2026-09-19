"""Shared pytest fixtures.

Integration tests require a live PostgreSQL database. Point ``OE_TEST_DATABASE_URL``
at it (default: ``postgresql+asyncpg://oe:oe@localhost:5432/oe_test``). The schema
is created once per session and each test runs inside a transaction that is rolled
back, so tests never leak state into one another.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.environ.get(
    "OE_TEST_DATABASE_URL",
    "postgresql+asyncpg://oe:oe@127.0.0.1:5432/oe_test",
)
os.environ.setdefault("OE_DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("OE_ENV", "test")
os.environ.setdefault("OE_SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnopqrstuvwxyz")
os.environ.setdefault("OE_BOOTSTRAP_ADMIN_USERNAME", "admin")
os.environ.setdefault("OE_BOOTSTRAP_ADMIN_PASSWORD", "admin")


def _database_available() -> bool:
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    async def _probe() -> bool:
        engine = create_async_engine(TEST_DATABASE_URL)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:  # noqa: BLE001
            return False
        finally:
            await engine.dispose()

    try:
        return asyncio.run(_probe())
    except Exception:  # noqa: BLE001
        return False


requires_db = pytest.mark.skipif(
    not _database_available(),
    reason="PostgreSQL test database is not available",
)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator:
    import oe_infrastructure.modules  # noqa: F401 — register all models
    from oe_infrastructure.modules.base import Base

    eng = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    """A session bound to a transaction that is rolled back after each test."""
    connection = await engine.connect()
    transaction = await connection.begin()
    maker = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    async with maker() as sess:
        yield sess
    await transaction.rollback()
    await connection.close()
