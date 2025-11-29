"""
Tests for user login endpoint.
"""
import pytest
import sys
from pathlib import Path
from httpx import AsyncClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestAuthLogin:
    """Tests for user login endpoint."""
    
    async def test_login_success(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test successful login."""
        # Register user first
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user(
            email="login@example.com",
            password="TestPassword123!",
        )
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "TestPassword123!",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"
        
        # Check refresh token in cookies
        cookies = response.cookies
        assert "refresh_token" in cookies or "refresh_token" in str(response.headers)
    
    async def test_login_user_not_found(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    async def test_login_wrong_password(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test login with wrong password."""
        seed = TestDataSeed(sqlite_uow)
        await seed.seed_user(
            email="wrongpass@example.com",
            password="CorrectPassword123!",
        )
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_login_case_insensitive_email(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test login with different case email."""
        seed = TestDataSeed(sqlite_uow)
        await seed.seed_user(
            email="caseinsensitive@example.com",
            password="TestPassword123!",
        )
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "CASEINSENSITIVE@EXAMPLE.COM",
                "password": "TestPassword123!",
            },
        )
        
        assert response.status_code == 200
