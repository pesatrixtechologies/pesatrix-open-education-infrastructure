"""Async SQLAlchemy database layer."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from oe_infrastructure.config import get_settings


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
    )


engine: AsyncEngine = _build_engine()
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a database session."""
    async with SessionLocal() as session:
        yield session


async def make_session() -> AsyncSession:
    """Create a standalone session (for scripts/CLI)."""
    return SessionLocal()


async def dispose_engine() -> None:
    await engine.dispose()


async def init_schema() -> None:
    """Create all tables. Intended for local development/tests.

    Production deployments MUST use Alembic migrations instead.
    See ``alembic/`` and ``docs/deployment/``.
    """
    # Importing the module registers all models on ``Base.metadata``.
    import oe_infrastructure.modules  # noqa: F401

    from oe_infrastructure.modules.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)