from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.logbook import LogBook

class LogbookRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, log: LogBook) -> None:
        self.session.add(log)
