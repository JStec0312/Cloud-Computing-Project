import sqlalchemy
from sqlalchemy import select, update
from src.domain.entities.refresh_token import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class RefreshTokenRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, refresh_token: RefreshToken) -> None:
        self.session.add(refresh_token)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        query = (select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1))
        result = (await self.session.execute(query)).scalars().first()

        if result:
            return result
        return None
    

    
    async def revoke_active(self, user_id: str, session_id: uuid.UUID, ) -> uuid.UUID | None:
        # return await self.session.execute(
        #     "UPDATE refresh_tokens" \
        #     " SET revoked_at = NOW()" \
        #     " WHERE user_id = :user_id" \
        #     " AND session_id = :session_id" \
        #     " AND revoked_at IS NULL" \
        #     " RETURNING id",
        # )
        stmt = update(RefreshToken).\
            where(
                RefreshToken.user_id == user_id,
                RefreshToken.session_id == session_id,
                RefreshToken.revoked_at.is_(None)
            ).\
            values(
                revoked_at=sqlalchemy.func.now()
            ).\
            returning(RefreshToken.id)
        result = await self.session.execute(stmt)
        revoked_token_id = result.scalar_one_or_none()
        return revoked_token_id
    
    async def revoke_all_user_tokens(self, user_id:str) -> None:
        # await self.session.execute(
        #     "UPDATE refresh_tokens" \
        #     " SET revoked_at = NOW()" \
        #     " WHERE user_id = :user_id" \
        #             )  
        stmt = update(RefreshToken).\
            where(
                RefreshToken.user_id == user_id
            ).\
            values(
                revoked_at=sqlalchemy.func.now()
            )
        await self.session.execute(stmt)     
        
    async def revoke_by_id(self, token_id: uuid.UUID) -> None:
        # await self.session.execute(
        #     "UPDATE refresh_tokens" \
        #     " SET revoked_at = NOW()" \
        #     " WHERE id = :token_id" \
        #     " RETURNING id",
        #     {"token_id": token_id}
        # )
        stmt = update(RefreshToken).\
            where(
                RefreshToken.id == token_id
            ).\
            values(
                revoked_at=sqlalchemy.func.now()
            )
        await self.session.execute(stmt)