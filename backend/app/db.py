"""
Async database engine, session factory, and FastAPI dependency.

Uses SQLAlchemy 2.0 async API with aiosqlite for local SQLite storage.
All table DDL is driven from the ORM models that inherit from ``Base``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


# ── Declarative base ────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── Engine & session factory ────────────────────────────────────
_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=False,
    # aiosqlite needs check_same_thread disabled
    connect_args={"check_same_thread": False},
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ──────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` and ensure it is closed after the request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Table initialisation ───────────────────────────────────────
async def init_db() -> None:
    """Create all tables that don't yet exist.

    Call once at application startup (e.g. in a ``lifespan`` handler).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
