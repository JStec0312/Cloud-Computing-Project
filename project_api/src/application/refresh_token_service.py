import datetime
from src.domain.entities.refresh_token import RefreshToken
from typing import Any, Mapping, Optional 
from src.infrastructure.uow import SqlAlchemyUoW
import uuid
import datetime
from src.infrastructure.security.token_hasher import TokenHasher

class RefreshTokenService:
    def __init__(self, hasher: TokenHasher):
        self._hasher: TokenHasher = hasher

    async def create_refresh_token(
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
    
    async def find_by_raw(
            self,
            uow: SqlAlchemyUoW,
            *,
            raw_token: str
    ) -> Optional[RefreshToken]:
        token_hash =  self._hasher.hash_token(raw_token)
        refresh_token = await uow.refresh_token.get_by_token_hash(token_hash)
        return refresh_token
    
    async def find_by_hashed(
            self,
            uow: SqlAlchemyUoW,
            *,
            token_hash: str
    ) -> Optional[RefreshToken]:
        refresh_token = await uow.refresh_token.get_by_token_hash(token_hash)
        return refresh_token

    async def get_current_refresh_token(
            self,
            uow: SqlAlchemyUoW,
            *,
            token_hash: str
    ) -> Optional[RefreshToken]:
        refresh_token = await uow.refresh_token.get_by_token_hash(token_hash)
        return refresh_token
    
    async def revoke_active_refresh_token(
            self,
            uow: SqlAlchemyUoW,
            *,
            user_id: uuid.UUID,
            session_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        revoked_token_id = await uow.refresh_token.revoke_active(
            user_id=user_id,
            session_id=session_id,
        )
        return revoked_token_id 
    
    async def revoke_all_user_tokens(
            self,
            uow: SqlAlchemyUoW,
            *,
            user_id: uuid.UUID,
    ) -> int:
        revoked_count = await uow.refresh_token.revoke_all_user_tokens(
            user_id=user_id,
        )
        return revoked_count
    
    async def revoke_token_by_id(
            self,
            uow: SqlAlchemyUoW,
            *,
            token_id: uuid.UUID,
    ) -> None:
        await uow.refresh_token.revoke_by_id(
            token_id=token_id,
        )