"""
Integration tests for file operations.
"""
import pytest
import sys
from pathlib import Path
from httpx import AsyncClient
import logging
from unittest.mock import patch

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.infrastructure.uow import SqlAlchemyUoW
from tests.seeds import TestDataSeed


class TestFileIntegration:
    """Integration tests for file operations."""
    
    async def test_complete_file_workflow(
        self,
        client: AsyncClient,
        sqlite_uow: SqlAlchemyUoW,
    ):
        """Test complete file workflow: upload -> list -> rename."""
        seed = TestDataSeed(sqlite_uow)
        user = await seed.seed_user()
        
        from src.api.auto_auth import current_user as real_current_user
        from src.api.schemas.users import UserFromToken
        
        async def fake_current_user():
            return UserFromToken(id=user.id, email=user.email, display_name=user.display_name)
        
        app.dependency_overrides[real_current_user] = fake_current_user
        
        try:
            # Step 1: Upload file
            with patch("src.infrastructure.storage.LocalBlobStorage.LocalBlobStorage.save") as mock_save:
                mock_save.return_value = "local_storage_data/test/workflow123"
                upload_response = await client.post(
                    "/api/v1/files/",
                    files = {"file": ("workflow.txt", b"abc content", "text/plain")}
                )
                logger.debug(f"Upload response status: {upload_response.status_code}, body: {upload_response.text}")
            
            assert upload_response.status_code == 201
            uploaded_file = upload_response.json()
            file_id = uploaded_file["id"]
            
            # Step 2: List files
            list_response = await client.get("/api/v1/files/")
            assert list_response.status_code == 200
            files = list_response.json()
            assert any(f["name"] == "workflow.txt" for f in files["items"])
            
            # Step 3: Rename file
            rename_response = await client.patch(
                f"/api/v1/files/{file_id}/rename",
                json={"new_name": "renamed_workflow.txt"},
            )
            assert rename_response.status_code == 200
            renamed = rename_response.json()
            assert renamed["name"] == "renamed_workflow.txt"
        finally:
            app.dependency_overrides.clear()
