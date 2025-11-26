# tests/conftest.py
import asyncio
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.deps import get_uow, get_auth_service  
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.db import Base 
from src.domain.entities.user import User


@pytest.fixture
async def memory_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,                  
        connect_args={"check_same_thread": False},
    )
    # utworzenie schematu
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture
async def session_factory(memory_engine):
    return async_sessionmaker(memory_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
def sqlite_uow(session_factory):
    return SqlAlchemyUoW(session_factory=session_factory)


@pytest.fixture
def app_with_sqlite_uow(sqlite_uow):
    app.dependency_overrides[get_uow] = lambda: sqlite_uow
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


from src.api.dependencies.auth import current_user as real_current_user

@pytest.fixture
def test_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="password",
    )

@pytest.fixture
def app_with_user(app_with_sqlite_uow, test_user):
    async def fake_current_user(*args, **kwargs):
        return test_user
    app.dependency_overrides[real_current_user] = fake_current_user
    try:
        yield app_with_sqlite_uow
    finally:
        app.dependency_overrides.pop(real_current_user, None)



@pytest.fixture
async def client(app_with_user):
    async with AsyncClient(app=app_with_user, base_url="http://test") as ac:
        yield ac
