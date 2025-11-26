from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.file import File

class FileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, file_id: str):
        stmnt = select(File).where(File.id == file_id)
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def add(self, file: File) -> None:
        self.session.add(file)
        return None

    async def get_by_owner_and_name(self, owner_id: str, name: str, parent_id: str | None) -> File | None:
        stmnt = select(File).where(File.owner_id == owner_id, File.name == name, File.parent_folder_id == parent_id)
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()