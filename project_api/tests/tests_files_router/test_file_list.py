"""
Tests for file listing endpoint.
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


class TestFileList:
    """Tests for file listing endpoint."""
    
    async def test_list_files_root(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test listing files in root folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        try:
            
            file1, _, _ = await seed.seed_file_with_version(
                owner_id=user.id,
                file_name="file1.txt",
            )
            file2, _, _ = await seed.seed_file_with_version(
                owner_id=user.id,
                file_name="file2.txt",
            )
        except Exception as e:
            logger.error(f"Error seeding files: {e}")
            raise
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get("/api/v1/files/", params={})
            logger.debug(f"List files response status: {response.status_code}, body: {response.text}")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2
            assert any(item["name"] == "file1.txt" for item in data["items"])
            assert any(item["name"] == "file2.txt" for item in data["items"])
        finally:
            app.dependency_overrides.clear()
    
    async def test_list_files_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test listing files in specific folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        folder = await seed.seed_folder(owner_id=user.id, name="documents")
        
        # Create file in folder
        file_in_folder, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="doc.txt",
        )
        
        async with sqlite_uow:
            file_in_folder.parent_folder_id = folder.id
            await sqlite_uow.commit()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/?folder_id={folder.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "breadcrumbs" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_list_files_empty_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test listing files in empty folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        empty_folder = await seed.seed_folder(owner_id=user.id, name="empty")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/?folder_id={empty_folder.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
        finally:
            app.dependency_overrides.clear()
    
    async def test_list_files_invalid_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test list fails with invalid folder ID."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_folder_id = uuid.uuid4()
            response = await client.get(f"/api/v1/files/?folder_id={fake_folder_id}")
            
            assert response.status_code in [400, 404, 200]
            if response.status_code == 200:
                data = response.json()
                assert "error" in data
        finally:
            app.dependency_overrides.clear()
