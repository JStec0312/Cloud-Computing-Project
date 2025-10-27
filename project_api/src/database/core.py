
from src.app_config import Settings
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated, AsyncGenerator
from fastapi import Depends

settings = Settings()
connection_string = settings.dsn_async()
engine = create_async_engine(connection_string)
AsyncSessionLocal = async_sessionmaker(bind = engine, autoflush=False, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session