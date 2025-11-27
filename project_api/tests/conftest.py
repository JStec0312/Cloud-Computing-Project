"""
Pytest configuration and global fixtures for testing.
"""
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import INET, JSONB

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.deps import get_uow, get_auth_service, get_filesvc
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.db.base import Base
from src.domain.entities.user import User
from src.infrastructure.security.password import PasswordHasher
from src.config.app_config import settings


# Create a no-op rate limiter for testing
class NoOpLimiter:
    """No-op limiter that allows all requests for testing."""
    def __call__(self, *args, **kwargs):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def limit(self, *args, **kwargs):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Override PostgreSQL-specific types for SQLite compatibility
@compiles(INET, 'sqlite')
def compile_inet_sqlite(type_, compiler, **kw):
    """Render INET as VARCHAR for SQLite compatibility."""
    return 'VARCHAR(45)'


@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Render JSONB as TEXT for SQLite compatibility."""
    return 'TEXT'


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    policy = asyncio.get_event_loop_policy()
    asyncio.set_event_loop_policy(policy)
    return policy


@pytest.fixture(scope="session")
def event_loop(event_loop_policy) -> Generator:
    """Create event loop for async tests."""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def session_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Register SQLite functions for PostgreSQL compatibility
    @event.listens_for(engine.sync_engine, "connect")
    def register_sqlite_functions(dbapi_conn, connection_record):
        """Register SQLite functions for PostgreSQL compatibility."""
        import datetime
        from math import floor
        
        # now() function - return ISO format string compatible with SQLite
        def now():
            return datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        dbapi_conn.create_function("now", 0, now)
        # floor() function
        dbapi_conn.create_function("floor", 1, floor)
    
    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def memory_engine(session_engine):
    """Get the session engine (for compatibility with existing fixture usage)."""
    return session_engine


@pytest.fixture
def session_factory(memory_engine) -> async_sessionmaker:
    """Create async session factory."""
    return async_sessionmaker(
        memory_engine, expire_on_commit=False, class_=AsyncSession
    )


@pytest.fixture
def sqlite_uow(session_factory) -> SqlAlchemyUoW:
    """Create UoW with SQLite session."""
    return SqlAlchemyUoW(session_factory=session_factory)


@pytest.fixture
def app_with_sqlite_uow(sqlite_uow):
    """Override app dependencies with test UoW and disable rate limiting."""
    # Override dependencies
    app.dependency_overrides[get_uow] = lambda: sqlite_uow
    
    # Set a huge rate limit for testing (essentially disabling it)
    settings.STANDARD_RATE_LIMIT = "999999/minute"
    
    # Disable rate limiting for tests
    app.state.limiter = NoOpLimiter()
    
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
        # Reset to original rate limit
        settings.STANDARD_RATE_LIMIT = "5/minute"


@pytest_asyncio.fixture
async def client(app_with_sqlite_uow) -> AsyncGenerator:
    """Create async HTTP test client."""
    transport = ASGITransport(app=app_with_sqlite_uow)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

        
@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_engine):
    """
    To fixture uruchamia się automatycznie po każdym teście.
    Czyści wszystkie tabele, ale zachowuje strukturę bazy.
    """
    yield
    
    # Ten kod wykona się PO każdym teście
    async with session_engine.begin() as conn:
        # Wyłączamy sprawdzanie kluczy obcych na chwilę, aby móc truncate'ować tabele w dowolnej kolejności
        await conn.execute(text("PRAGMA foreign_keys = OFF;"))
        
        for table in Base.metadata.sorted_tables:
            await conn.execute(text(f"DELETE FROM {table.name};"))
            # Dla SQLite warto też zresetować liczniki autoincrement
            await conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table.name}';"))

        await conn.execute(text("PRAGMA foreign_keys = ON;"))