"""
Tests for file version download endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient
import logging
from unittest.mock import patch, AsyncMock

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestFileVersionDownload:
    """Tests for file version download endpoint."""
    
    async def test_download_file_version_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful download of a specific file version."""
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
                yield b"version 1 content"
            
            # Upload a file first
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file_v1"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("test.txt", b"version 1 content")},
                )
            
            assert upload_response.status_code == 201
            file_data = upload_response.json()
            file_id = file_data["id"]
            
            # Get file versions to find version_id
            versions_response = await client.get(f"/api/v1/files/{file_id}/versions")
            assert versions_response.status_code == 200
            versions = versions_response.json()
            assert len(versions) > 0
            version_id = versions[0]["id"]
            
            # Download specific version
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/versions/{version_id}/download")
            
            assert response.status_code == 200
            assert "content-disposition" in response.headers
            assert "attachment" in response.headers["content-disposition"]
            # Version filename should include version number
            assert "_v" in response.headers["content-disposition"]
            assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_version_nonexistent_file(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading version of nonexistent file returns 404."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_file_id = uuid.uuid4()
            fake_version_id = uuid.uuid4()
            
            response = await client.get(f"/api/v1/files/{fake_file_id}/versions/{fake_version_id}/download")
            
            assert response.status_code == 404
            assert "detail" in response.json()
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_version_nonexistent_version(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading nonexistent version of existing file returns 404."""
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
                yield b"file content"
            
            # Upload a file first
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file_version"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("test.txt", b"file content")},
                )
            
            assert upload_response.status_code == 201
            file_id = upload_response.json()["id"]
            
            fake_version_id = uuid.uuid4()
            response = await client.get(f"/api/v1/files/{file_id}/versions/{fake_version_id}/download")
            
            assert response.status_code == 404
            assert "detail" in response.json()
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_version_unauthorized_user(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading version as different user returns 403."""
        seed = TestDataSeed(sqlite_uow)
        owner = await seed.seed_user()
        other_user = await seed.seed_user(email="other@example.com")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def owner_current_user():
            return UserFromToken(id=owner.id, email=owner.email, display_name=owner.display_name)
        
        async def other_current_user():
            return UserFromToken(id=other_user.id, email=other_user.email, display_name=other_user.display_name)
        
        app.dependency_overrides[real_current_user] = owner_current_user
        
        try:
            # Mock function to return file content
            async def mock_get(self, file_hash: str):
                yield b"owner's file content"
            
            # Owner uploads file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/owner_file"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("owner.txt", b"owner's file content")},
                )
            
            assert upload_response.status_code == 201
            file_data = upload_response.json()
            file_id = file_data["id"]
            
            # Get versions as owner
            versions_response = await client.get(f"/api/v1/files/{file_id}/versions")
            assert versions_response.status_code == 200
            versions = versions_response.json()
            assert len(versions) > 0
            version_id = versions[0]["id"]
            
            # Try to download as different user
            app.dependency_overrides[real_current_user] = other_current_user
            
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/versions/{version_id}/download")
            
            assert response.status_code == 403
            assert "detail" in response.json()
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_version_with_extension(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test that version filename includes extension and version number."""
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
                yield b"PDF version 1 content"
            
            # Upload PDF file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/pdf_v1"
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("document.pdf", b"PDF version 1 content")},
                )
            
            assert upload_response.status_code == 201
            file_id = upload_response.json()["id"]
            
            # Get versions
            versions_response = await client.get(f"/api/v1/files/{file_id}/versions")
            assert versions_response.status_code == 200
            versions = versions_response.json()
            version_id = versions[0]["id"]
            
            # Download version
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/versions/{version_id}/download")
            
            assert response.status_code == 200
            disposition = response.headers.get("content-disposition", "")
            # Should contain version indicator and extension
            assert "_v" in disposition
            assert "document" in disposition or "pdf" in disposition.lower()
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_multiple_file_versions(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading multiple versions of the same file."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Mock function to return file content based on hash
            async def mock_get(self, file_hash: str):
                yield b"version content: " + file_hash.encode()[:10]
            
            # Upload initial file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file_multi_v1"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("multi.txt", b"version 1")},
                )
            
            assert upload_response.status_code == 201
            file_id = upload_response.json()["id"]
            
            # Upload second version
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/file_multi_v2"
                
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("multi.txt", b"version 2")},
                )
            
            # Get all versions
            versions_response = await client.get(f"/api/v1/files/{file_id}/versions")
            assert versions_response.status_code == 200
            versions = versions_response.json()
            assert len(versions) >= 1
            
            # Download all versions
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                for version in versions:
                    response = await client.get(f"/api/v1/files/{file_id}/versions/{version['id']}/download")
                    assert response.status_code == 200
                    disposition = response.headers.get("content-disposition", "")
                    # Each version should have its version number
                    assert "_v" in disposition
                    assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_version_correct_mime_type(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test that version download returns correct content-type."""
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
                yield b"PDF content binary data"
            
            # Upload PDF file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/mime_test.pdf"
                upload_response = await client.post(
                    "/api/v1/files/",
                    files={"file": ("test.pdf", b"PDF content binary data")},
                )
            
            assert upload_response.status_code == 201
            file_id = upload_response.json()["id"]
            
            # Get versions
            versions_response = await client.get(f"/api/v1/files/{file_id}/versions")
            assert versions_response.status_code == 200
            versions = versions_response.json()
            version_id = versions[0]["id"]
            
            # Download version and check content-type
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.get", mock_get):
                response = await client.get(f"/api/v1/files/{file_id}/versions/{version_id}/download")
            
            assert response.status_code == 200
            # Should have correct content-type for PDF
            content_type = response.headers.get("content-type", "")
            assert content_type in ["application/pdf", "application/octet-stream"]
        finally:
            app.dependency_overrides.clear()
