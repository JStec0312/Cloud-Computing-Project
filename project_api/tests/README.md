"""
Test Documentation and Guidelines.

## Test Structure

This project uses clean architecture patterns for testing:

### Directories
- `test_*.py` - Test modules for routers and services
- `factories.py` - Entity factory classes for test object creation
- `seeds.py` - TestDataSeed class for populating test databases
- `helpers.py` - Helper classes for common test operations
- `conftest.py` - Pytest configuration and global fixtures

### Core Components

#### 1. Factories (factories.py)
Factory classes that create domain entities with sensible defaults:
- UserFactory - Creates User entities
- FileFactory - Creates File entities
- BlobFactory - Creates Blob entities
- FileVersionFactory - Creates FileVersion entities
- SessionFactory - Creates Session entities
- RefreshTokenFactory - Creates RefreshToken entities

Usage:
```python
user = await UserFactory.create(email="test@example.com")
blob = BlobFactory.create(sha256="hash123")
```

#### 2. Seeds (seeds.py)
TestDataSeed class for populating databases with test data:
- seed_user() - Create and persist user
- seed_file() - Create and persist file
- seed_folder() - Create and persist folder
- seed_file_with_version() - Create file with version and blob
- seed_blob() - Create and persist blob

Usage:
```python
seed = TestDataSeed(uow)
user = await seed.seed_user(email="test@example.com")
file, version, blob = await seed.seed_file_with_version(owner_id=user.id)
```

#### 3. Helpers (helpers.py)
Helper classes for common test operations:

**AuthTestHelper:**
- create_access_token(user_id) - Generate valid JWT access token
- create_refresh_token(user_id) - Generate valid refresh token

**FileTestHelper:**
- create_file_structure() - Create complete folder/file hierarchy

**RequestHelper:**
- get_auth_headers(token) - Get Authorization header
- get_client_info() - Get mock client info

**AssertionHelper:**
- assert_user_response() - Validate user response format
- assert_file_response() - Validate file response format
- assert_error_response() - Validate error response format

#### 4. Fixtures (conftest.py)
Global pytest fixtures available to all tests:
- `event_loop` - Async event loop for session
- `memory_engine` - In-memory SQLite database
- `session_factory` - AsyncSessionMaker for UoW
- `sqlite_uow` - SqlAlchemyUoW instance
- `app_with_sqlite_uow` - FastAPI app with test UoW override
- `client` - AsyncClient for HTTP testing

### Test Modules

#### test_auth_router.py
Tests for authentication endpoints:

**TestAuthRegister:**
- test_register_user_success - Valid registration
- test_register_duplicate_email - Duplicate email error
- test_register_user_email_normalized - Email lowercasing
- test_register_missing_fields - Validation error

**TestAuthLogin:**
- test_login_success - Valid login
- test_login_user_not_found - User not found error
- test_login_wrong_password - Invalid password error
- test_login_case_insensitive_email - Case-insensitive email

**TestAuthRefresh:**
- test_refresh_token_missing - Missing token error
- test_refresh_token_success - Valid refresh

**TestAuthIntegration:**
- test_register_login_flow - Complete register->login flow

#### test_files_router.py
Tests for file management endpoints:

**TestFileUpload:**
- test_upload_file_success - Valid file upload
- test_upload_file_too_large - File size limit
- test_upload_to_folder - Upload to specific folder
- test_upload_invalid_parent_folder - Invalid parent error

**TestFileList:**
- test_list_files_root - List root files
- test_list_files_folder - List folder contents
- test_list_files_empty_folder - Empty folder handling
- test_list_files_invalid_folder - Invalid folder error

**TestFileRename:**
- test_rename_file_success - Valid rename
- test_rename_to_existing_name - Duplicate name error
- test_rename_nonexistent_file - File not found error

**TestFileIntegration:**
- test_complete_file_workflow - Upload->list->rename flow

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test module:
```bash
pytest tests/test_auth_router.py
```

### Run specific test class:
```bash
pytest tests/test_auth_router.py::TestAuthRegister
```

### Run specific test:
```bash
pytest tests/test_auth_router.py::TestAuthRegister::test_register_user_success
```

### Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Run with verbose output:
```bash
pytest -v
```

### Run with logging:
```bash
pytest -v --log-cli-level=DEBUG
```

## Best Practices

1. **Use Factories for Entity Creation:**
   ```python
   user = await UserFactory.create(email="custom@example.com")
   ```

2. **Use Seeds for Database Population:**
   ```python
   seed = TestDataSeed(sqlite_uow)
   user = await seed.seed_user()
   file, version, blob = await seed.seed_file_with_version(owner_id=user.id)
   ```

3. **Use Helpers for Common Operations:**
   ```python
   token = AuthTestHelper.create_access_token(user.id)
   headers = RequestHelper.get_auth_headers(token)
   ```

4. **Mock External Dependencies:**
   ```python
   with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
       mock_save.return_value = "local_storage_data/test/file"
       response = await client.post("/files/", ...)
   ```

5. **Override App Dependencies in Tests:**
   ```python
   from src.api.auto_auth import current_user as real_current_user
   
   async def fake_current_user(*args, **kwargs):
       return UserFromToken(id=user.id, email=user.email)
   
   app.dependency_overrides[real_current_user] = fake_current_user
   try:
       # test code
   finally:
       app.dependency_overrides.clear()
   ```

6. **Test Both Happy Paths and Error Cases:**
   - Success scenarios
   - Missing required fields
   - Invalid data
   - Duplicate entries
   - Access control violations

7. **Clean Up After Tests:**
   Always clear dependency overrides in finally blocks.

## Example Test

```python
async def test_upload_and_list_files(client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
    \"\"\"Complete workflow: upload file and verify listing.\"\"\"
    # Setup
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    # Override auth
    from src.api.auto_auth import current_user
    from src.api.schemas.users import UserFromToken
    
    async def fake_auth(*args, **kwargs):
        return UserFromToken(id=user.id, email=user.email)
    
    app.dependency_overrides[current_user] = fake_auth
    
    try:
        # Step 1: Upload
        with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock:
            mock.return_value = "path/to/file"
            
            upload_response = await client.post(
                "/files/",
                data={"parent_id": None},
                files={"file": ("test.txt", b"content")},
            )
        
        assert upload_response.status_code == 201
        
        # Step 2: List
        list_response = await client.get("/files/")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "test.txt"
    finally:
        app.dependency_overrides.clear()
```
"""
