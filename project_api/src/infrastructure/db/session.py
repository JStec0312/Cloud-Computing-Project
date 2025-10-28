from __future__ import annotations  # (opcjonalnie, wtedy adnotacje nie są ewaluowane w runtime)

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config.app_config import Settings

settings = Settings()
DATABASE_URL = settings.dsn_async()

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
