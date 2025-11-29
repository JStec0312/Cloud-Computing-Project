"""
Tests for token refresh endpoint.
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
