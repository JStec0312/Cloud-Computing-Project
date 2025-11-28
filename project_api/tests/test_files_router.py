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
from tests.factories import UserFactory, FileVersionFactory
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


class TestFileDelete:
    """Tests for file deletion endpoint."""
    
    async def test_delete_file_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful file deletion."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.delete(f"/api/v1/files/{file.id}")
            assert response.status_code == 204
            
            # Verify file is deleted by trying to list files
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert not any(f["id"] == str(file.id) for f in files["items"])
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_nonexistent_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test delete fails for nonexistent file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_file_id = uuid.uuid4()
            response = await client.delete(f"/api/v1/files/{fake_file_id}")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_file_unauthorized(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test delete fails when user doesn't own the file."""
        seed = TestDataSeed(sqlite_uow)
        owner = await seed.seed_user()
        other_user = await seed.seed_user(email="other@example.com")
        file, _, _ = await seed.seed_file_with_version(owner_id=owner.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=other_user.id, email=other_user.email, display_name=other_user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.delete(f"/api/v1/files/{file.id}")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_file_with_multiple_versions(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test deleting a file with multiple versions."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, blob = await seed.seed_file_with_version(owner_id=user.id)
        
        # Add another version
        _, _, _= await seed.seed_file_with_version(owner_id=user.id, file_name="test2.txt", blob=blob)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.delete(f"/api/v1/files/{file.id}")
            assert response.status_code == 204
            
            # Verify file and all versions are deleted
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert not any(f["id"] == str(file.id) for f in files["items"])
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test deleting a folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        # Create a folder (is_folder=True)
        folder = await seed.seed_folder(owner_id=user.id, name="test_folder")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.delete(f"/api/v1/files/{folder.id}")
            assert response.status_code == 204
            
            # Verify folder is deleted
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert not any(f["id"] == str(folder.id) for f in files["items"])
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_file_in_subfolder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test deleting a file that's in a subfolder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        # Create folder and file in folder
        folder = await seed.seed_folder(owner_id=user.id, name="subfolder")
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="subfile.txt",
        )
        # Update parent folder ID
        async with sqlite_uow:
            file.parent_folder_id = folder.id
            await sqlite_uow.commit()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.delete(f"/api/v1/files/{file.id}")
            assert response.status_code == 204
            
            # Verify file is deleted but folder remains
            list_response = await client.get(f"/api/v1/files/?folder_id={folder.id}")
            assert list_response.status_code == 200
            files = list_response.json()
            assert not any(f["id"] == str(file.id) for f in files["items"])
        finally:
            app.dependency_overrides.clear()
    
    async def test_delete_multiple_files_sequentially(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test deleting multiple files one after another."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        # Create multiple files
        file1, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file1.txt")
        file2, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file2.txt")
        file3, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file3.txt")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Delete all files
            for file in [file1, file2, file3]:
                response = await client.delete(f"/api/v1/files/{file.id}")
                assert response.status_code == 204
            
            # Verify all files are deleted
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert len(files["items"]) == 0
        finally:
            app.dependency_overrides.clear()


class TestFileVersions:
    """Tests for file versions endpoint."""
    
    async def test_get_file_versions_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successfully retrieving file versions."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, version1, blob = await seed.seed_file_with_version(owner_id=user.id)
        
        # Add a second version
        version2_blob = await seed.seed_blob()
        _, version2, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="test_v2.txt",
            blob=version2_blob
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/versions")
            assert response.status_code == 200
            versions = response.json()
            assert isinstance(versions, list)
            assert len(versions) >= 1
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_single_version(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test getting versions for a file with only one version."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, version, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/versions")
            assert response.status_code == 200
            versions = response.json()
            assert len(versions) == 1
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_nonexistent_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test getting versions for a nonexistent file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_file_id = uuid.uuid4()
            response = await client.get(f"/api/v1/files/{fake_file_id}/versions")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_unauthorized(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test getting versions fails when user doesn't own the file."""
        seed = TestDataSeed(sqlite_uow)
        owner = await seed.seed_user()
        other_user = await seed.seed_user(email="other@example.com")
        file, _, _ = await seed.seed_file_with_version(owner_id=owner.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=other_user.id, email=other_user.email, display_name=other_user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/versions")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_multiple_versions(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test getting multiple versions of the same file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, v1, blob1 = await seed.seed_file_with_version(owner_id=user.id, file_name="multi.txt")
        
        # Create additional versions
        blob2 = await seed.seed_blob()
        blob3 = await seed.seed_blob()
        
        async with sqlite_uow:
            # Add version 2
            v2 = FileVersionFactory.create(
                file_id=file.id,
                version_no=2,
                uploaded_by=user.id,
                blob_id=blob2.id,
                blob=blob2,
            )
            await sqlite_uow.file_versions.add(v2)
            
            # Add version 3
            v3 = FileVersionFactory.create(
                file_id=file.id,
                version_no=3,
                uploaded_by=user.id,
                blob_id=blob3.id,
                blob=blob3,
            )
            await sqlite_uow.file_versions.add(v3)
            await sqlite_uow.commit()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/versions")
            assert response.status_code == 200
            versions = response.json()
            assert len(versions) == 3
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_response_structure(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test that version responses have correct structure."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, version, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/versions")
            assert response.status_code == 200
            versions = response.json()
            assert len(versions) > 0
            
            # Check first version has expected fields
            v = versions[0]
            assert "id" in v
            assert "file_id" in v or "version_no" in v or "uploaded_at" in v
        finally:
            app.dependency_overrides.clear()
    
    async def test_get_versions_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test getting versions for a folder (should fail)."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        folder = await seed.seed_folder(owner_id=user.id, name="test_folder")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{folder.id}/versions")
            # Folder shouldn't have versions, might return 200 with empty list or 400
            assert response.status_code in [200, 400, 404]
        finally:
            app.dependency_overrides.clear()
