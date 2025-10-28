from typing import Any, Mapping, Optional 
from src.infrastructure.uow import SqlAlchemyUoW
from src.domain.enums.op_type import OpType
from src.domain.entities.logbook import LogBook
import uuid
from src.domain.entities.session import Session

class SessionService:
    async def create_session(
            self,
            uow: SqlAlchemyUoW,
            *,
            user_id: uuid.UUID,
            ip: str,
            user_agent: str,
    ) -> Session:
        user_session = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            ip_inet=ip,
            user_agent=user_agent,
        )
        await uow.user_session.add(user_session)
        return user_session