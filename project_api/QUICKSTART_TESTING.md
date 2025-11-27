# Quick Start Guide - Testing

## Installation

```bash
# Install testing dependencies
pip install -r requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth_router.py

# Run specific test class
pytest tests/test_auth_router.py::TestAuthRegister

# Run specific test
pytest tests/test_auth_router.py::TestAuthRegister::test_register_user_success

# Run with coverage report
pytest --cov=src --cov-report=html

# Run only auth tests
pytest -m auth

# Run only file tests
pytest -m files

# Run only integration tests
pytest -m integration
```

## Project Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── factories.py             # Entity factories (UserFactory, FileFactory, etc.)
├── seeds.py                 # TestDataSeed class for database population
├── helpers.py               # Helper classes for testing
├── examples.py              # Example test patterns
├── README.md                # Detailed test documentation
├── test_auth_router.py      # Authentication endpoint tests
├── test_files_router.py     # File management endpoint tests
└── __init__.py              # Package initialization
```

## Key Components

### Factories (factories.py)
Create test entities with sensible defaults:
```python
from tests.factories import UserFactory, FileFactory

user = await UserFactory.create(email="test@example.com")
file = FileFactory.create(owner_id=user.id, name="test.txt")
```

### Seeds (seeds.py)
Populate database with test data:
```python
from tests.seeds import TestDataSeed

seed = TestDataSeed(uow)
user = await seed.seed_user()
file, version, blob = await seed.seed_file_with_version(owner_id=user.id)
```

### Helpers (helpers.py)
Common testing operations:
```python
from tests.helpers import AuthTestHelper, RequestHelper

token = AuthTestHelper.create_access_token(user_id)
headers = RequestHelper.get_auth_headers(token)
```

### Fixtures (conftest.py)
Global fixtures for all tests:
```python
async def test_something(client: AsyncClient, sqlite_uow: SqlAlchemyUoW):
    # client = AsyncClient for HTTP testing
    # sqlite_uow = In-memory SQLite UoW
    pass
```

## Writing a New Test

### 1. Basic Test Template
```python
async def test_my_feature(
    client: AsyncClient,
    sqlite_uow: SqlAlchemyUoW,
):
    """Test description."""
    # Setup
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    # Execute
    response = await client.get("/endpoint")
    
    # Assert
    assert response.status_code == 200
```

### 2. Test with Authentication
```python
async def test_authenticated_endpoint(
    client: AsyncClient,
    sqlite_uow: SqlAlchemyUoW,
):
    """Test authenticated endpoint."""
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    # Override auth dependency
    from src.api.auto_auth import current_user
    from src.api.schemas.users import UserFromToken
    
    async def fake_auth(*args, **kwargs):
        return UserFromToken(id=user.id, email=user.email)
    
    app.dependency_overrides[current_user] = fake_auth
    
    try:
        response = await client.get("/protected-endpoint")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
```

### 3. Test with Mocking
```python
from unittest.mock import patch

async def test_with_mocked_storage(
    client: AsyncClient,
    sqlite_uow: SqlAlchemyUoW,
):
    """Test with mocked external service."""
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    
    with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock:
        mock.return_value = "path/to/file"
        
        response = await client.post(
            "/files/",
            data={"parent_id": None},
            files={"file": ("test.txt", b"content")},
        )
        
        assert response.status_code == 201
        assert mock.called
```

## Coverage Analysis

```bash
# Generate coverage report
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## Common Patterns

### Testing Success Cases
- Valid input → successful response
- Verify response format and data

### Testing Error Cases
- Missing required fields → 422 error
- Duplicate data → 409 error
- Non-existent resource → 404 error
- Invalid credentials → 401 error
- Access denied → 403 error

### Testing Workflows
- Multi-step operations (register → login → access protected endpoint)
- File operations (upload → list → rename → delete)

## Tips and Tricks

### 1. Use Parameterized Tests
```python
@pytest.mark.parametrize("email,valid", [
    ("test@example.com", True),
    ("invalid-email", False),
])
async def test_email_validation(email, valid, client):
    # test with multiple inputs
    pass
```

### 2. Create Custom Fixtures
```python
@pytest.fixture
async def user_with_files(sqlite_uow):
    seed = TestDataSeed(sqlite_uow)
    user = await seed.seed_user()
    file = await seed.seed_file(owner_id=user.id)
    return {"user": user, "file": file}
```

### 3. Use Markers
```python
@pytest.mark.auth
async def test_login():
    # Run with: pytest -m auth
    pass
```

### 4. Debug Tests
```bash
# Run with verbose output and print statements
pytest -v -s

# Run with logging
pytest -v --log-cli-level=DEBUG

# Run one test at a time
pytest -v tests/test_auth_router.py::TestAuthRegister::test_login_success
```

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Ensure you're running pytest from project root:
```bash
cd /path/to/project_api
pytest
```

### Issue: "No tests found"
**Solution:** Check test discovery:
```bash
# List all discovered tests
pytest --collect-only

# Ensure test files are named test_*.py
# Ensure test functions are named test_*
```

### Issue: Async tests failing
**Solution:** Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Issue: Database conflicts
**Solution:** Each test gets isolated in-memory SQLite database from fixtures

## Next Steps

1. ✅ Run all tests: `pytest -v`
2. ✅ Check coverage: `pytest --cov=src`
3. ✅ Write new tests following patterns in examples.py
4. ✅ Update factories/seeds when entities change
5. ✅ Keep tests organized by router/feature

## Resources

- Full documentation: `tests/README.md`
- Example tests: `tests/examples.py`
- Auth tests: `tests/test_auth_router.py`
- File tests: `tests/test_files_router.py`
- Pytest docs: https://docs.pytest.org/
