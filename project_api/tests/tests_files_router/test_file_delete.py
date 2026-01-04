"""
Tests for file deletion endpoint.
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

@pytest.mark.asyncio
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
        await seed.seed_file_with_version(owner_id=user.id, file_name="test2.txt", blob=blob)
        
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
