from sqlalchemy import select, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.file import File
from typing import Optional, Sequence
from uuid import UUID
from src.domain.entities.file_version import FileVersion

class FileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, file_id: str):
        stmnt = (
            select(File)
            .options(selectinload(File.current_version).selectinload(FileVersion.blob))
            .where(File.id == file_id)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def add(self, file: File) -> None:
        self.session.add(file)
        return None

    async def get_by_owner_and_name(self, owner_id: str, name: str, parent_id: str | None) -> File | None:
        stmnt = (
            select(File)
            .options(selectinload(File.current_version).selectinload(FileVersion.blob))
            .where(File.owner_id == owner_id, File.name == name, File.parent_folder_id == parent_id)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()
    
    async def list_in_folder(self, owner_id: str, folder_id: str | None) -> list[File]:
        stmnt = (
            select(File)
            .options(selectinload(File.current_version).selectinload(FileVersion.blob))
            .where(File.owner_id == owner_id, File.parent_folder_id == folder_id)
        )
        result = await self.session.execute(stmnt)
        return result.scalars().all()
    

    async def get_folder_content(self, user_id:str, folder_id: Optional[UUID]) -> Sequence[File]:
        stmnt = (
            select(File)
            .options(
                selectinload(File.current_version).selectinload(FileVersion.blob)
            )
            .where(File.owner_id == user_id, File.parent_folder_id == folder_id)
            .order_by(
                desc(File.is_folder),
                asc(File.name)
            )
        )
        result = await self.session.execute(stmnt)
        return result.scalars().all()
    

    async def get_by_name_in_folder(
        self, 
        user_id: UUID, 
        name: str, 
        parent_id: Optional[UUID]
    ) -> Optional[File]:
        query = (
            select(File)
            .options(selectinload(File.current_version).selectinload(FileVersion.blob))
            .where(
                File.owner_id == user_id,
                File.name == name,
                File.parent_folder_id == parent_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()


    async def delete(self, file) -> None:
        await self.session.delete(file)
        return None
    
    
    async def get_by_name_and_parent(
        self,
        owner_id: UUID,
        name: str,
        parent_folder_id: Optional[UUID]
    ) -> Optional[File]:
        stmnt = (
            select(File)
            .where(
                File.owner_id == owner_id,
                File.name == name,
                File.parent_folder_id == parent_folder_id
            )
        )
        result = await self.session.execute(stmnt)
        return result.scalars().first()
    
    