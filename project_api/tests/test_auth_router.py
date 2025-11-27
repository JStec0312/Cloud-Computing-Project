"""
Unit tests for authentication router endpoints.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.deps import get_uow, get_auth_service
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.security.password import PasswordHasher
from src.application.auth_service import AuthService
from tests.seeds import TestDataSeed
from tests.helpers import AuthTestHelper, AssertionHelper, RequestHelper
from tests.factories import UserFactory


class TestAuthRegister:
    """Tests for user registration endpoint."""
    
    async def test_register_user_success(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "display_name": "New User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["display_name"] == "New User"
        assert "id" in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test registration with duplicate email fails."""
        seed = TestDataSeed(sqlite_uow)
        await seed.seed_user(email="existing@example.com")
        
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "display_name": "Another User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
    
    async def test_register_user_email_normalized(self, client: AsyncClient):
        """Test that email is normalized (lowercased)."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "TestUser@Example.COM",
                "display_name": "Test User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "testuser@example.com"
    
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration fails with missing fields."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                # Missing display_name and password
            },
        )
        
        assert response.status_code == 422


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


class TestAuthRefresh:
    """Tests for token refresh endpoint."""
    
    async def test_refresh_token_missing(self, client: AsyncClient):
        """Test refresh fails without refresh token."""
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "refresh token" in data["detail"].lower()
    
    async def test_refresh_token_success(self, client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
        """Test successful token refresh."""
        # Create and login user
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user(
            email="refresh@example.com",
            password="TestPassword123!",
        )
        
        # Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "TestPassword123!",
            },
        )
        
        assert login_response.status_code == 200
        
        # Extract original access token
        original_access_token = login_response.json()["access_token"]
        
        # Attempt refresh
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            cookies=client.cookies,
        )
        
        # Should succeed and return new access token
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data["user"]["id"] == str(user.id)


class TestAuthIntegration:
    """Integration tests for complete auth flows."""
    
    async def test_register_login_flow(self, client: AsyncClient):
        """Test complete register -> login flow."""
        # Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "flow@example.com",
                "display_name": "Flow User",
                "password": "FlowPassword123!",
            },
        )
        
        assert register_response.status_code == 201
        
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "flow@example.com",
                "password": "FlowPassword123!",
            },
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["user"]["email"] == "flow@example.com"
        assert "access_token" in login_data
