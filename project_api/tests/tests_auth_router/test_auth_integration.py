"""
Integration tests for complete auth flows.
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

@pytest.mark.asyncio
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
