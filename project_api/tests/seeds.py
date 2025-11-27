"""
Test seeds and data builders for consistent test state setup.
"""
import uuid
from typing import Optional
from src.infrastructure.uow import SqlAlchemyUoW
from src.domain.entities.user import User
from src.domain.entities.file import File
from src.domain.entities.blob import Blob
from src.domain.entities.file_version import FileVersion
from src.domain.entities.session import Session
from src.domain.entities.refresh_token import RefreshToken
from tests.factories import (
    UserFactory,
    BlobFactory,
    FileFactory,
    FileVersionFactory,
    SessionFactory,
    RefreshTokenFactory,
)


class TestDataSeed:
    """Seed class for populating test databases with consistent data."""
    
    def __init__(self, uow: SqlAlchemyUoW):
        self.uow = uow
    
    async def seed_user(
        self,
        email: str = "test@example.com",
        display_name: str = "Test User",
        password: str = "TestPassword123!",
    ) -> User:
        """Seed a user into the database."""
        user = await UserFactory.create(
            email=email,
            display_name=display_name,
            password=password,
        )
        async with self.uow:
            await self.uow.users.add(user)
            await self.uow.commit()
        return user
    
    async def seed_users(self, count: int = 3) -> list[User]:
        """Seed multiple users."""
        users = []
        for i in range(count):
            user = await self.seed_user(
                email=f"user{i}@example.com",
                display_name=f"User {i}",
            )
            users.append(user)
        return users
    
    async def seed_blob(
        self,
        sha256: Optional[str] = None,
        size_bytes: int = 1024,
        storage_path: str = "local_storage_data/test/blob",
    ) -> Blob:
        """Seed a blob into the database."""
        if sha256 is None:
            sha256 = uuid.uuid4().hex * 2  
        blob = BlobFactory.create(
            sha256=sha256,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        async with self.uow:
            await self.uow.blobs.add(blob)
            await self.uow.commit()
        return blob
    
    async def seed_file(
        self,
        owner_id: uuid.UUID,
        name: str = "test.txt",
        mime_type: str = "text/plain",
        is_folder: bool = False,
        parent_folder_id: Optional[uuid.UUID] = None,
    ) -> File:
        """Seed a file into the database."""
        file = FileFactory.create(
            owner_id=owner_id,
            name=name,
            mime_type=mime_type,
            is_folder=is_folder,
            parent_folder_id=parent_folder_id,
        )
        async with self.uow:
            await self.uow.files.add(file)
            await self.uow.commit()
        return file
    
    async def seed_folder(
        self,
        owner_id: uuid.UUID,
        name: str = "test_folder",
        parent_folder_id: Optional[uuid.UUID] = None,
    ) -> File:
        """Seed a folder (is_folder=True) into the database."""
        return await self.seed_file(
            owner_id=owner_id,
            name=name,
            is_folder=True,
            parent_folder_id=parent_folder_id,
        )
    
    async def seed_file_with_version(
        self,
        owner_id: uuid.UUID,
        blob: Optional[Blob] = None,
        file_name: str = "test.txt",
        version_no: int = 1,
    ) -> tuple[File, FileVersion, Blob]:
        """Seed a complete file with version and blob."""
        if not blob:
            blob = await self.seed_blob()
        
        file = await self.seed_file(
            owner_id=owner_id,
            name=file_name,
        )
        
        file_version = FileVersionFactory.create(
            file_id=file.id,
            version_no=version_no,
            uploaded_by=owner_id,
            blob_id=blob.id,
            blob=blob,
        )
        
        async with self.uow:
            await self.uow.file_versions.add(file_version)
            file.current_version_id = file_version.id
            await self.uow.commit()
        
        return file, file_version, blob
    
    async def seed_session(
        self,
        user_id: uuid.UUID,
        ip_address: str = "127.0.0.1",
        user_agent: str = "TestAgent/1.0",
    ) -> Session:
        """Seed a session into the database."""
        session = SessionFactory.create(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        async with self.uow:
            await self.uow.session.add(session)
            await self.uow.commit()
        return session
    
    async def seed_refresh_token(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        token_hash: str = "test_token_hash",
    ) -> RefreshToken:
        """Seed a refresh token into the database."""
        refresh_token = RefreshTokenFactory.create(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
        )
        async with self.uow:
            await self.uow.refresh_token.add(refresh_token)
            await self.uow.commit()
        return refresh_token
