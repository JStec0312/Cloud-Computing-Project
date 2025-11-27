"""
Example test patterns and common scenarios.

This file demonstrates best practices for writing tests with the clean architecture.
"""

# ============================================================================
# EXAMPLE 1: Using Factories to Create Entities
# ============================================================================

from tests.factories import UserFactory, FileFactory, BlobFactory

# Basic usage with defaults
user = await UserFactory.create()
# Returns: User(id=uuid4, email='test@example.com', display_name='Test User', ...)

# Custom attributes
user = await UserFactory.create(
    email="alice@example.com",
    display_name="Alice Smith",
    password="CustomPassword123!"
)

# File with custom properties
file = FileFactory.create(
    owner_id=user.id,
    name="document.pdf",
    mime_type="application/pdf",
    is_folder=False,
)

# Blob with custom hash
blob = BlobFactory.create(
    sha256="abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
    size_bytes=2048,
    storage_path="local_storage_data/custom/path",
)


# ============================================================================
# EXAMPLE 2: Using TestDataSeed for Database Setup
# ============================================================================

from tests.seeds import TestDataSeed
from src.infrastructure.uow import SqlAlchemyUoW

async def setup_test_data(uow: SqlAlchemyUoW):
    """Populate database with test data."""
    seed = TestDataSeed(uow)
    
    # Create a user
    user = await seed.seed_user(
        email="testuser@example.com",
        display_name="Test User",
    )
    
    # Create multiple users
    users = await seed.seed_users(count=5)
    
    # Create a folder
    folder = await seed.seed_folder(
        owner_id=user.id,
        name="My Documents",
    )
    
    # Create a file with complete hierarchy
    file, version, blob = await seed.seed_file_with_version(
        owner_id=user.id,
        file_name="report.docx",
    )
    
    # Create a session
    session = await seed.seed_session(
        user_id=user.id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
    )
    
    # Create a refresh token
    token = await seed.seed_refresh_token(
        user_id=user.id,
        session_id=session.id,
        token_hash="hashed_token_123",
    )
    
    return {
        "user": user,
        "folder": folder,
        "file": file,
        "blob": blob,
        "session": session,
        "token": token,
    }


# ============================================================================
# EXAMPLE 3: Using Helpers in Tests
# ============================================================================

from tests.helpers import (
    AuthTestHelper,
    FileTestHelper,
    RequestHelper,
    AssertionHelper,
)

async def test_file_operations():
    """Example test using helpers."""
    
    # Create auth token
    user_id = uuid.uuid4()
    access_token = AuthTestHelper.create_access_token(user_id)
    
    # Get headers with token
    headers = RequestHelper.get_auth_headers(access_token)
    # Returns: {"Authorization": "Bearer <token>"}
    
    # Get mock client info
    client_info = RequestHelper.get_client_info()
    # Returns: {"host": "127.0.0.1", "user_agent": "TestAgent/1.0"}
    
    # Use in assertions
    response = {"id": str(user_id), "email": "test@example.com"}
    # AssertionHelper.assert_user_response(response, user)


# ============================================================================
# EXAMPLE 4: Complete Test with Mocking
# ============================================================================

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from src.api.app import app
from src.infrastructure.uow import SqlAlchemyUoW

async def test_file_upload_with_storage_mock(
    client: AsyncClient,
    sqlite_uow: SqlAlchemyUoW,
):
    """Example test with storage mocking."""
    
    # Setup data
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    # Override authentication
    from src.api.auto_auth import current_user
    from src.api.schemas.users import UserFromToken
    
    async def fake_auth(*args, **kwargs):
        return UserFromToken(id=user.id, email=user.email)
    
    app.dependency_overrides[current_user] = fake_auth
    
    try:
        # Mock external storage service
        with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
            # Configure mock
            mock_save.return_value = "local_storage_data/test/abc123"
            
            # Make request
            response = await client.post(
                "/files/",
                data={"parent_id": None},
                files={"file": ("test.pdf", b"PDF content here")},
            )
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test.pdf"
        assert "id" in data
        
        # Verify mock was called
        assert mock_save.called
        
    finally:
        # Clean up
        app.dependency_overrides.clear()


# ============================================================================
# EXAMPLE 5: Testing Complete Workflows
# ============================================================================

async def test_auth_flow_integration(client: AsyncClient):
    """Example integration test for complete auth flow."""
    
    # Step 1: Register
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "display_name": "New User",
            "password": "SecurePassword123!",
        },
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    user_id = user_data["id"]
    
    # Step 2: Login
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    access_token = login_data["access_token"]
    
    # Step 3: Use token in authenticated request
    headers = RequestHelper.get_auth_headers(access_token)
    authorized_response = await client.get("/files/", headers=headers)
    assert authorized_response.status_code == 200


# ============================================================================
# EXAMPLE 6: Parameterized Tests
# ============================================================================

import pytest

@pytest.mark.parametrize("email,password,should_succeed", [
    ("valid@example.com", "ValidPassword123!", True),
    ("", "ValidPassword123!", False),
    ("valid@example.com", "", False),
    ("invalid-email", "ValidPassword123!", False),
])
async def test_register_various_inputs(
    email: str,
    password: str,
    should_succeed: bool,
    client: AsyncClient,
):
    """Test registration with various inputs."""
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "display_name": "Test User",
            "password": password,
        },
    )
    
    if should_succeed:
        assert response.status_code in [200, 201]
    else:
        assert response.status_code >= 400


# ============================================================================
# EXAMPLE 7: Testing Error Scenarios
# ============================================================================

async def test_file_operations_error_scenarios(
    client: AsyncClient,
    sqlite_uow: SqlAlchemyUoW,
):
    """Test various error scenarios."""
    
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    from src.api.auto_auth import current_user
    from src.api.schemas.users import UserFromToken
    
    async def fake_auth(*args, **kwargs):
        return UserFromToken(id=user.id, email=user.email)
    
    app.dependency_overrides[current_user] = fake_auth
    
    try:
        # Test: Upload to non-existent folder
        fake_folder_id = uuid.uuid4()
        response = await client.post(
            "/files/",
            data={"parent_id": str(fake_folder_id)},
            files={"file": ("test.txt", b"content")},
        )
        assert response.status_code in [400, 404, 200]
        
        # Test: Rename non-existent file
        fake_file_id = uuid.uuid4()
        response = await client.patch(
            f"/files/{fake_file_id}/rename",
            json={"new_name": "new_name.txt"},
        )
        assert response.status_code in [404, 200]
        
        # Test: List non-existent folder
        response = await client.get(f"/files/?folder_id={fake_folder_id}")
        assert response.status_code in [400, 404, 200]
        
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# EXAMPLE 8: Fixture Usage for Common Setup
# ============================================================================

@pytest.fixture
async def authenticated_user(sqlite_uow: SqlAlchemyUoW):
    """Fixture that provides authenticated user."""
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    return user


@pytest.fixture
async def user_with_files(sqlite_uow: SqlAlchemyUoW):
    """Fixture that provides user with file structure."""
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
    
    return {
        "user": user,
        "files": [file1, file2],
    }


# Using fixtures in tests
async def test_with_fixture(user_with_files):
    """Test using custom fixture."""
    user = user_with_files["user"]
    files = user_with_files["files"]
    
    assert user.id is not None
    assert len(files) == 2
