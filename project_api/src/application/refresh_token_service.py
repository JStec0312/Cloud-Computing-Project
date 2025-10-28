import datetime
from src.domain.entities.refresh_token import RefreshToken
from typing import Any, Mapping, Optional 
from src.infrastructure.uow import SqlAlchemyUoW
import uuid
import datetime

class RefreshTokenService:
    async  def create_refresh_token(
            self,
            uow: SqlAlchemyUoW,
            *,
            user_id: uuid.UUID,
            session_id: uuid.UUID,
            revoked_id: Optional[uuid.UUID],
            token_hash: str,
            expires_at: datetime.datetime
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            session_id=session_id,
            revoked_id=revoked_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        await uow.refresh_token.add(refresh_token)
        return refresh_token
    
    async def get_current_refresh_token(
            self,
            uow: SqlAlchemyUoW,
            *,
            token_hash: str
    ) -> Optional[RefreshToken]:
        refresh_token = await uow.refresh_token.get_by_token_hash(token_hash)
        return refresh_token