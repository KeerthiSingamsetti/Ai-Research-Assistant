from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.config import settings
from backend.database.models import Base

# Ensure the SQLite URL is structured for async use (aiosqlite)
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite:///"):
    # Convert standard sqlite URL to aiosqlite driver
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create Async Engine
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# Async Session Factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db() -> None:
    """Initializes database schema and creates all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for Async DB Session.

    Yields:
        An active AsyncSession instance.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
