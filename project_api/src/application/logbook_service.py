import alembic
from typing import Any, Mapping, Optional 
from src.infrastructure.uow import SqlAlchemyUoW
from src.domain.enums.op_type import OpType
from src.domain.entities.logbook import LogBook
import uuid

class LogbookService:
    async def register_log(
            self,
            uow: SqlAlchemyUoW,
            *,
            op_type: OpType,
            remote_addr: str,
            user_agent: str,
            details: Mapping[str, Any],
            file_id: Optional[uuid.UUID] = None,
            user_id: Optional[uuid.UUID] = None,
            session_id: Optional[uuid.UUID] = None
    ) -> None:
        value = op_type.value
        log = LogBook(
            op_type=value,
            remote_addr=remote_addr,
            user_agent=user_agent,
            details=details,
            user_id=user_id,
            session_id=session_id,
            file_id=file_id
        )
        await uow.logbook.add(log)

    