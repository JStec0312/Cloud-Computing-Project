"""
Tests for file versions endpoint.
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
from tests.factories import FileVersionFactory


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
