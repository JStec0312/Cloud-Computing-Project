from src.domain.entities.session import Session as UserSession
from sqlalchemy.ext.asyncio import AsyncSession
class SessionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_session: UserSession) -> None:
        self.session.add(user_session)