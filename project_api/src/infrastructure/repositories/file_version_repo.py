from src.domain.entities.file_version import FileVersion
from sqlalchemy.ext.asyncio import AsyncSession


class FileVersionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, file_version: FileVersion) -> None:
        self.session.add(file_version)
        return None
    