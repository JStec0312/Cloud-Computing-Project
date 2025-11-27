"""
Factories for creating test entities using clean architecture patterns.
"""
import uuid
from typing import Optional
from src.domain.entities.user import User
from src.domain.entities.file import File
from src.domain.entities.file_version import FileVersion
from src.domain.entities.blob import Blob
from src.domain.entities.session import Session
from src.domain.entities.refresh_token import RefreshToken
from src.infrastructure.security.password import PasswordHasher


class UserFactory:
    """Factory for creating test User entities."""
    
    @staticmethod
    async def create(
        id: Optional[uuid.UUID] = None,
        email: str = "test@example.com",
        display_name: str = "Test User",
        password: str = "TestPassword123!",
        **kwargs
    ) -> User:
        """Create a user with optional overrides."""
        hasher = PasswordHasher()
        hashed = await hasher.hash(password)
        
        return User(
            id=id or uuid.uuid4(),
            email=email,
            display_name=display_name,
            hashed_password=hashed,
            **kwargs
        )


class BlobFactory:
    """Factory for creating test Blob entities."""
    
    @staticmethod
    def create(
        id: Optional[uuid.UUID] = None,
        sha256: str = "abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
        size_bytes: int = 1024,
        storage_path: str = "local_storage_data/test/blob",
        **kwargs
    ) -> Blob:
        """Create a blob with optional overrides."""
        return Blob(
            id=id or uuid.uuid4(),
            sha256=sha256,
            size_bytes=size_bytes,
            storage_path=storage_path,
            **kwargs
        )


class FileVersionFactory:
    """Factory for creating test FileVersion entities."""
    
    @staticmethod
    def create(
        id: Optional[uuid.UUID] = None,
        file_id: Optional[uuid.UUID] = None,
        version_no: int = 1,
        uploaded_by: Optional[uuid.UUID] = None,
        blob_id: Optional[uuid.UUID] = None,
        blob: Optional[Blob] = None,
        **kwargs
    ) -> FileVersion:
        """Create a file version with optional overrides."""
        if blob:
            blob_id = blob.id
        
        return FileVersion(
            id=id or uuid.uuid4(),
            file_id=file_id or uuid.uuid4(),
            version_no=version_no,
            uploaded_by=uploaded_by or uuid.uuid4(),
            blob_id=blob_id or uuid.uuid4(),
            blob=blob,
            **kwargs
        )


class FileFactory:
    """Factory for creating test File entities."""
    
    @staticmethod
    def create(
        id: Optional[uuid.UUID] = None,
        owner_id: Optional[uuid.UUID] = None,
        name: str = "test_file.txt",
        mime_type: str = "text/plain",
        is_folder: bool = False,
        parent_folder_id: Optional[uuid.UUID] = None,
        current_version_id: Optional[uuid.UUID] = None,
        current_version: Optional[FileVersion] = None,
        **kwargs
    ) -> File:
        """Create a file with optional overrides."""
        if current_version:
            current_version_id = current_version.id
        
        return File(
            id=id or uuid.uuid4(),
            owner_id=owner_id or uuid.uuid4(),
            name=name,
            mime_type=mime_type,
            is_folder=is_folder,
            parent_folder_id=parent_folder_id,
            current_version_id=current_version_id,
            current_version=current_version,
            **kwargs
        )


class SessionFactory:
    """Factory for creating test Session entities."""
    
    @staticmethod
    def create(
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: str = "127.0.0.1",
        user_agent: str = "TestAgent/1.0",
        **kwargs
    ) -> Session:
        """Create a session with optional overrides."""
        return Session(
            id=id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )


class RefreshTokenFactory:
    """Factory for creating test RefreshToken entities."""
    
    @staticmethod
    def create(
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        token_hash: str = "hashed_token_abc123",
        **kwargs
    ) -> RefreshToken:
        """Create a refresh token with optional overrides."""
        return RefreshToken(
            id=id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            session_id=session_id or uuid.uuid4(),
            token_hash=token_hash,
            **kwargs
        )
