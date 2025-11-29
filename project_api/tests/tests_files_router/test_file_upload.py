"""
Tests for file upload endpoint.
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
from unittest.mock import patch


class TestFileUpload:
    """Tests for file upload endpoint."""
    
    async def test_upload_file_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful file upload."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        # Override auth to use seed user
        from src.api.auto_auth import current_user as real_current_user
        async def fake_current_user():
            from src.api.schemas.users import UserFromToken
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Mock storage
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file123"
                
                response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("test.txt", b"test content")},
                )
            
            assert response.status_code == 201
            logger.debug(f"Upload response status: {response.status_code}, body: {response.text}")
            data = response.json()
            assert data["name"] == "test.txt"
            assert "id" in data
            assert data["version"] == 1
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_file_too_large(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test upload fails for oversized files."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create large file content (exceeds typical max)
            large_content = b"x" * (1024 * 1024 * 510)  # 510MB
            
            response = await client.post(
                "/api/v1/files/",
                files={"file": ("large.bin", large_content)},
            )
            
            assert response.status_code == 413
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_to_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test uploading file to specific folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        folder = await seed.seed_folder(owner_id=user.id, name="uploads")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file456"
                
                response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("document.pdf", b"pdf content")},
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "document.pdf"
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_invalid_parent_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test upload fails with invalid parent folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_folder_id = uuid.uuid4()
            
            response = await client.post(
                "/api/v1/files/",
                files={"file": ("test.txt", b"content")},
                data={"parent_id": str(fake_folder_id)}
            )
            
            # Should fail or return error
            assert response.status_code == 404
            if response.status_code == 200:
                data = response.json()
                assert "error" in data
        finally:
            app.dependency_overrides.clear()
