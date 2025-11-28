from sqlalchemy import select
from src.domain.entities.file_version import FileVersion
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


class FileVersionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, file_version: FileVersion) -> None:
        self.session.add(file_version)
        return None
    
    async def list_by_file_id(self, file_id: str) -> list[FileVersion]:
        stmt = select(FileVersion).where(FileVersion.file_id == file_id).options(joinedload(FileVersion.blob))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    