"""
Tests for folder creation endpoint.
"""
import pytest
import sys
from pathlib import Path
import uuid
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestFolderCreate:
    """Tests for folder creation endpoint."""
    
    async def test_create_folder_success(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test successful folder creation in root."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "My Documents",
                    "parent_folder_id": None,
                },
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "My Documents"
            assert data["is_folder"] is True
            assert "id" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_in_subfolder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating a folder inside an existing folder."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        parent_folder = await seed.seed_folder(owner_id=user.id, name="Parent")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Subfolder",
                    "parent_folder_id": str(parent_folder.id),
                },
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Subfolder"
            assert data["is_folder"] is True
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_duplicate_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder with duplicate name fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        await seed.seed_folder(owner_id=user.id, name="Documents")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Documents",
                    "parent_folder_id": None,
                },
            )
            
            assert response.status_code in [409, 400]
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_invalid_parent(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder with invalid parent folder ID fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            fake_parent_id = uuid.uuid4()
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "New Folder",
                    "parent_folder_id": str(fake_parent_id),
                },
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_parent_not_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder when parent is a file (not a folder) fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        file, _, _ = await seed.seed_file_with_version(owner_id=user.id)
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Invalid Parent",
                    "parent_folder_id": str(file.id),
                },
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_missing_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder without name fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "parent_folder_id": None,
                },
            )
            
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_empty_name(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder with empty name fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "",
                    "parent_folder_id": None,
                },
            )
            
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_name_too_long(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder with name exceeding max length fails."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            long_name = "a" * 300  # Exceeds 255 character limit
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": long_name,
                    "parent_folder_id": None,
                },
            )
            
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_folder_in_other_user_folder(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating folder in another user's folder fails."""
        seed = TestDataSeed(sqlite_uow)
        owner = await seed.seed_user()
        other_user = await seed.seed_user(email="other@example.com")
        other_folder = await seed.seed_folder(owner_id=owner.id, name="Owner's Folder")
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=other_user.id, email=other_user.email, display_name=other_user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Unauthorized Folder",
                    "parent_folder_id": str(other_folder.id),
                },
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_multiple_folders_in_root(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating multiple folders in root directory."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            folder_names = ["Documents", "Downloads", "Projects"]
            created_folders = []
            
            for name in folder_names:
                response = await client.post(
                    "/api/v1/files/folders",
                    json={
                        "folder_name": name,
                        "parent_folder_id": None,
                    },
                )
                assert response.status_code == 201
                created_folders.append(response.json())
            
            # Verify all folders were created
            assert len(created_folders) == 3
            for i, folder in enumerate(created_folders):
                assert folder["name"] == folder_names[i]
                assert folder["is_folder"] is True
        finally:
            app.dependency_overrides.clear()
    
    async def test_create_nested_folders(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test creating nested folder structure."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Create root folder
            root_response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Root",
                    "parent_folder_id": None,
                },
            )
            assert root_response.status_code == 201
            root_id = root_response.json()["id"]
            
            # Create subfolder in root
            sub_response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Subfolder",
                    "parent_folder_id": str(root_id),
                },
            )
            assert sub_response.status_code == 201
            sub_id = sub_response.json()["id"]
            
            # Create sub-subfolder
            subsub_response = await client.post(
                "/api/v1/files/folders",
                json={
                    "folder_name": "Sub-Subfolder",
                    "parent_id": str(sub_id),
                },
            )
            assert subsub_response.status_code == 201
            assert subsub_response.json()["name"] == "Sub-Subfolder"
        finally:
            app.dependency_overrides.clear()
