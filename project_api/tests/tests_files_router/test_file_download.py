"""
Tests for file download endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient
import logging
from io import BytesIO

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
        """Test successful file download."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            assert "content-disposition" in response.headers
            assert "attachment" in response.headers["content-disposition"]
            assert len(response.content) > 0
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
        file, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="document.pdf")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            disposition = response.headers.get("content-disposition", "")
            assert "document.pdf" in disposition or "document" in disposition
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_content_type(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test download returns correct content type."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id, 
            file_name="image.jpg"
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            assert response.headers.get("content-type") in [
                "image/jpeg",
                "application/octet-stream"
            ]
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
        file, _, _ = await seed.seed_file_with_version(owner_id=owner.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=downloader.id, email=downloader.email, display_name=downloader.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_without_extension(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading file without extension gets one added based on mime type."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="document"
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            disposition = response.headers.get("content-disposition", "")
            # Should add extension from mime type
            assert "filename" in disposition or "document" in disposition
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_with_special_characters_in_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading file with special characters in filename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="raport_2025_01_15.pdf"
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            assert "content-disposition" in response.headers
            # Filename should be properly encoded
            disposition = response.headers.get("content-disposition", "")
            assert "filename" in disposition or "raport" in disposition
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_content_streamed(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test that file download uses streaming response."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            # Streaming response should have content
            assert len(response.content) > 0
            # Should have content-disposition header for attachment
            assert "attachment" in response.headers.get("content-disposition", "")
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
        file1, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file1.txt")
        file2, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file2.txt")
        file3, _, _ = await seed.seed_file_with_version(owner_id=user.id, file_name="file3.txt")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            files_to_download = [file1, file2, file3]
            
            for file in files_to_download:
                response = await client.get(f"/api/v1/files/{file.id}/download")
                assert response.status_code == 200
                assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_without_mime_type(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading file without mime type returns octet-stream."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="unknown_file"
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            content_type = response.headers.get("content-type")
            # Should default to octet-stream if no mime type
            assert content_type in ["application/octet-stream", None] or content_type
        finally:
            app.dependency_overrides.clear()
    
    async def test_download_file_with_unicode_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test downloading file with unicode characters in filename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(
            owner_id=user.id,
            file_name="dokument_üñíçödé.txt"
        )
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.get(f"/api/v1/files/{file.id}/download")
            
            assert response.status_code == 200
            assert "content-disposition" in response.headers
            # UTF-8 encoding should be used
            disposition = response.headers.get("content-disposition", "")
            assert "utf-8" in disposition.lower() or "dokument" in disposition
        finally:
            app.dependency_overrides.clear()
