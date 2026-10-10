"""
Async database engine, session factory, and FastAPI dependency.

Supports both Supabase PostgreSQL (via asyncpg) and local SQLite (via aiosqlite).
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

db_url = _settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

is_sqlite = db_url.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args["check_same_thread"] = False
else:
    # Transaction poolers require statement_cache_size=0 for asyncpg
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
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
    """Create all tables that don't yet exist and run initial seeder.

    Call once at application startup (e.g. in a ``lifespan`` handler).
    """
    import app.models  # noqa: F401 - Register all models with Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial data
    try:
        import importlib.util
        from pathlib import Path
        seed_path = Path(__file__).parent / "db" / "seed.py"
        if seed_path.exists():
            spec = importlib.util.spec_from_file_location("app_db_seed", seed_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                await mod.seed_database()
    except Exception as e:
        print(f"Database seed notice: {e}")

