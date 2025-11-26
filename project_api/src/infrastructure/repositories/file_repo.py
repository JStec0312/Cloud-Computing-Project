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
