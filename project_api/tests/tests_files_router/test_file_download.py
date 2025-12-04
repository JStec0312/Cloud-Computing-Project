"""
Tests for file download endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient
import logging
from unittest.mock import patch

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestFileDownload:
    """Tests for file download endpoint."""
    
    async def test_download_file_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful file download after upload."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Mock function to return file content
            async def mock_get(self, file_hash: str):
                yield b"test content here"
            
            # Upload a file first
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file123"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("test.txt", b"test content here")},
                )
            
            assert upload_response.status_code == 201
            file_data = upload_response.json()
            file_id = file_data["id"]
            
            # Now download it with mocked get
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/download")
            
            assert response.status_code == 200
            assert "content-disposition" in response.headers
            assert "attachment" in response.headers["content-disposition"]
            assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_nonexistent_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading nonexistent file returns 404."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_file_id = uuid.uuid4()
            response = await client.get(f"/api/v1/files/{fake_file_id}/download")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_unauthorized(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading another user's file returns 403."""
        seed = TestDataSeed(sqlite_uow)
        owner = await seed.seed_user()
        downloader = await seed.seed_user(email="downloader@example.com")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        # First, upload a file as owner
        async def fake_current_user_owner():
            return UserFromToken(id=owner.id, email=owner.email, display_name=owner.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user_owner
        
        with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
            mock_save.return_value = "local_storage_data/test/file_owner"
            upload_response = await client.post(
                "/api/v1/files/",
                files={"file": ("owner_file.txt", b"owner content")},
            )
        
        assert upload_response.status_code == 201
        file_id = upload_response.json()["id"]
        
        # Now try to download as different user
        async def fake_current_user_downloader():
            return UserFromToken(id=downloader.id, email=downloader.email, display_name=downloader.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user_downloader
        
        try:
            response = await client.get(f"/api/v1/files/{file_id}/download")
            
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_with_extension(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading file preserves extension in filename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Mock function to return file content
            async def mock_get(self, file_hash: str):
                yield b"PDF content here"
            
            # Upload PDF file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/pdf_file"
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("document.pdf", b"PDF content here")},
                )
            
            assert upload_response.status_code == 201
            file_id = upload_response.json()["id"]
            
            # Download and check extension preserved
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/download")
            
            assert response.status_code == 200
            disposition = response.headers.get("content-disposition", "")
            assert "document" in disposition or "pdf" in disposition.lower()
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_multiple_files(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading multiple different files sequentially."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Mock function to return file content
            async def mock_get(self, file_hash: str):
                # Return different content based on hash for realism
                yield b"file content for hash " + file_hash.encode()[:10]
            
            file_ids = []
            
            # Upload 3 files
            for i, filename in enumerate(["file1.txt", "file2.txt", "file3.txt"]):
                with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                    mock_save.return_value = f"local_storage_data/test/file{i}"
                    upload_response = await client.post(
                        "/api/v1/files/",
                        files={"file": (filename, f"content {i}".encode())},
                    )
                assert upload_response.status_code == 201
                file_ids.append(upload_response.json()["id"])
            
            # Download all of them
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                for file_id in file_ids:
                    response = await client.get(f"/api/v1/files/{file_id}/download")
                    assert response.status_code == 200
                    assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()
