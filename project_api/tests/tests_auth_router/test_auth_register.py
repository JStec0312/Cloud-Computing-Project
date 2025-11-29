"""
Tests for user registration endpoint.
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
