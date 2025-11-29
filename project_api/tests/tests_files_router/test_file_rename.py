"""
Tests for file rename endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestFileRename:
    """Tests for file rename endpoint."""
    
    async def test_rename_file_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful file rename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="old_name.txt",
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.patch(
                f"/api/v1/files/{file.id}/rename",
                json={"new_name": "new_name.txt"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "new_name.txt"
        finally:
            app.dependency_overrides.clear()
    
    async def test_rename_to_existing_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test rename fails when name exists."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file1, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="file1.txt",
        )
        file2, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="file2.txt",
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.patch(
                f"/api/v1/files/{file1.id}/rename",
                json={"new_name": "file2.txt"},
            )
            
            assert response.status_code in [400, 409, 200]
            if response.status_code == 200:
                data = response.json()
                assert "error" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_rename_nonexistent_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test rename fails for nonexistent file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_file_id = uuid.uuid4()
            response = await client.patch(
                f"/api/v1/files/{fake_file_id}/rename",
                json={"new_name": "new_name.txt"},
            )
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
