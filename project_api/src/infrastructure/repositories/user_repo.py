from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User  

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: User) -> None:
        self.session.add(user)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        return (await self.get_by_email(email)) is not None

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()