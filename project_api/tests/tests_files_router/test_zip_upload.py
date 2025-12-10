"""
Tests for ZIP file upload endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
import io
import zipfile
from httpx import AsyncClient
import logging
from unittest.mock import patch, AsyncMock, MagicMock

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestZipUpload:
    """Tests for ZIP file upload endpoint."""
    
    async def test_upload_zip_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful ZIP file upload and extraction."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a simple ZIP file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr("file1.txt", b"content of file 1")
                zip_file.writestr("file2.txt", b"content of file 2")
            zip_buffer.seek(0)
            
            # Mock the storage and service
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile"
                
                response = await client.post(
                    "/api/v1/files/zip",
                    files={"file": ("test.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "id" in data or "status" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_invalid_content_type(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload with invalid content type."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a text file (not a ZIP)
            response = await client.post(
                "/api/v1/files/zip",
                files={"file": ("test.txt", b"this is not a zip file", "text/plain")},
            )
            
            # Should fail with BadZipFile error (500)
            assert response.status_code >= 400
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_without_parent_id(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload to root folder (no parent_id)."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr("rootfile.txt", b"root content")
            zip_buffer.seek(0)
            
            # Mock storage
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile2"
                
                # Upload without parent_id - should go to root
                response = await client.post(
                    "/api/v1/files/zip",
                    files={"file": ("root.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_to_specific_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload to specific parent folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        folder = await seed.seed_folder(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr("folderfile.txt", b"folder content")
            zip_buffer.seek(0)
            
            # Mock storage
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile3"
                
                # Upload to specific folder
                response = await client.post(
                    "/api/v1/files/zip",
                    data={"parent_id": str(folder.id)},
                    files={"file": ("folder.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_nested_structure(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload with nested folder structure."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP with nested structure
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr("folder1/file1.txt", b"nested file 1")
                zip_file.writestr("folder1/subfolder/file2.txt", b"deeply nested file")
                zip_file.writestr("file3.txt", b"root level file")
            zip_buffer.seek(0)
            
            # Mock storage
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile_nested"
                
                response = await client.post(
                    "/api/v1/files/zip",
                    files={"file": ("nested.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_empty_zip(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test upload of empty ZIP file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create an empty ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                pass  # Empty ZIP
            zip_buffer.seek(0)
            
            # Mock storage
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile_empty"
                
                response = await client.post(
                    "/api/v1/files/zip",
                    files={"file": ("empty.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            # Empty ZIP should still process (may or may not create files)
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_invalid_parent_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload to non-existent parent folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        fake_folder_id = uuid.uuid4()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr("file.txt", b"content")
            zip_buffer.seek(0)
            
            response = await client.post(
                "/api/v1/files/zip",
                data={"parent_id": str(fake_folder_id)},
                files={"file": ("test.zip", zip_buffer.getvalue(), "application/zip")},
            )
            
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_unauthorized_parent_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload to folder owned by different user."""
        seed = TestDataSeed(sqlite_uow)
        user1 = await seed.seed_user()
        
        # Create second user with unique email
        from src.domain.entities.user import User
        user2 = User(
            id=uuid.uuid4(),
            email=f"user2-{uuid.uuid4()}@example.com",
            display_name="User Two",
            hashed_password="fake_hash"
        )
        async with sqlite_uow:
            await sqlite_uow.users.add(user2)
            await sqlite_uow.commit()
        
        folder = await seed.seed_folder(owner_id=user2.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user1.id, email=user1.email, display_name=user1.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr("file.txt", b"content")
            zip_buffer.seek(0)
            
            response = await client.post(
                "/api/v1/files/zip",
                data={"parent_id": str(folder.id)},
                files={"file": ("test.zip", zip_buffer.getvalue(), "application/zip")},
            )
            
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
    
    async def test_upload_zip_large_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test ZIP upload with large file content."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create a ZIP with a large file (1MB)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                large_content = b"x" * (1024 * 1024)  # 1MB
                zip_file.writestr("largefile.bin", large_content)
            zip_buffer.seek(0)
            
            # Mock storage
            async def mock_get(self, file_hash: str):
                yield b"test file content"
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save, \
                 patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                mock_save.return_value = "local_storage_data/test/zipfile_large"
                
                response = await client.post(
                    "/api/v1/files/zip",
                    files={"file": ("large.zip", zip_buffer.getvalue(), "application/zip")},
                )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
