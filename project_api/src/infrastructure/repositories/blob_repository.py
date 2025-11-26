from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.blob import Blob
from sqlalchemy import select


class BlobRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_hash(self, sha256_hash: str) -> Blob | None:
        stmnt = select(Blob).where(Blob.sha256 == sha256_hash)
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()
    async def add(self, blob: Blob) -> None:
        self.session.add(blob)
        return None