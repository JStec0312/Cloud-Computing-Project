"""
Test helpers for common testing operations.
"""
import uuid
from typing import Optional
from src.infrastructure.uow import SqlAlchemyUoW
from src.domain.entities.user import User
from src.infrastructure.security.access_token import (
    create_access_token,
    create_refresh_token,
)
from tests.seeds import TestDataSeed


class AuthTestHelper:
    """Helper methods for authentication testing."""
    
    @staticmethod
    def create_access_token(user_id: uuid.UUID) -> str:
        """Create a valid access token for testing."""
        return create_access_token(user_id=user_id)
    
    @staticmethod
    def create_refresh_token(user_id: uuid.UUID) -> str:
        """Create a valid refresh token for testing."""
        return create_refresh_token(user_id=user_id)


class FileTestHelper:
    """Helper methods for file testing."""
    
    @staticmethod
    async def create_file_structure(
        uow: SqlAlchemyUoW,
        owner_id: uuid.UUID,
        folder_count: int = 2,
        files_per_folder: int = 3,
    ) -> dict:
        """Create a complete file/folder structure for testing."""
        seed = TestDataSeed(uow)
        structure = {
            "folders": [],
            "files": [],
        }
        
        # Create root folders
        for i in range(folder_count):
            folder = await seed.seed_folder(
                owner_id=owner_id,
                name=f"folder_{i}",
            )
            structure["folders"].append(folder)
            
            # Create files in each folder
            for j in range(files_per_folder):
                file, _, _ = await seed.seed_file_with_version(
                    owner_id=owner_id,
                    file_name=f"file_{j}.txt",
                )
                file.parent_folder_id = folder.id
                async with uow:
                    await uow.commit()
                structure["files"].append(file)
        
        return structure


class RequestHelper:
    """Helper methods for building test requests."""
    
    @staticmethod
    def get_auth_headers(access_token: str) -> dict:
        """Get headers with Bearer token."""
        return {"Authorization": f"Bearer {access_token}"}
    
    @staticmethod
    def get_client_info() -> dict:
        """Get mock client info."""
        return {
            "host": "127.0.0.1",
            "user_agent": "TestAgent/1.0",
        }


class AssertionHelper:
    """Helper methods for common assertions."""
    
    @staticmethod
    def assert_user_response(response_data: dict, user: User):
        """Assert user response format and content."""
        assert response_data["id"] == str(user.id)
        assert response_data["email"] == user.email
        assert response_data["display_name"] == user.display_name
    
    @staticmethod
    def assert_file_response(response_data: dict, file_id: uuid.UUID, name: str):
        """Assert file response format and content."""
        assert response_data["id"] == str(file_id)
        assert response_data["name"] == name
    
    @staticmethod
    def assert_error_response(response_data: dict, expected_error: str):
        """Assert error response format."""
        assert "error" in response_data
        assert expected_error.lower() in response_data["error"].lower()
