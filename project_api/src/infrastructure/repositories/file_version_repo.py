from sqlalchemy import select
from src.domain.entities.file_version import FileVersion
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Optional
from uuid import UUID


class FileVersionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, file_version: FileVersion) -> None:
        self.session.add(file_version)
        return None
    
    async def get_by_id(self, version_id: UUID) -> Optional[FileVersion]:
        """Get a file version by its ID."""
        stmt = select(FileVersion).where(FileVersion.id == version_id).options(joinedload(FileVersion.blob))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_by_file_id(self, file_id: str) -> list[FileVersion]:
        stmt = select(FileVersion).where(FileVersion.file_id == file_id).options(joinedload(FileVersion.blob))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    