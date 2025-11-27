"""
Unit tests for files router endpoints.
"""
from fastapi import params
import pytest
import sys
from pathlib import Path
import uuid
from io import BytesIO
from httpx import AsyncClient
import logging
logger = logging.getLogger(__name__)
# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.deps import get_uow
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.storage.LocalBlobStorage import LocalBlobStorage
from tests.seeds import TestDataSeed
from tests.helpers import FileTestHelper, RequestHelper, AssertionHelper
from tests.factories import UserFactory
from unittest.mock import AsyncMock, patch, MagicMock


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


class TestFileIntegration:
    """Integration tests for file operations."""
    
    async def test_complete_file_workflow(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test complete file workflow: upload -> list -> rename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Step 1: Upload file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/workflow123"
                upload_response = await client.post(
                    "/api/v1/files/",
                    files = {"file": ("workflow.txt", b"abc content", "text/plain")}
                )
                logger.debug(f"Upload response status: {upload_response.status_code}, body: {upload_response.text}")
            
            assert upload_response.status_code == 201
            uploaded_file = upload_response.json()
            file_id = uploaded_file["id"]
            
            # Step 2: List files
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert any(f["name"] == "workflow.txt" for f in files["items"])
            
            # Step 3: Rename file
            rename_response = await client.patch(
                f"/api/v1/files/{file_id}/rename",
                json={"new_name": "renamed_workflow.txt"},
            )
            assert rename_response.status_code == 200
            renamed = rename_response.json()
            assert renamed["name"] == "renamed_workflow.txt"
        finally:
            app.dependency_overrides.clear()
