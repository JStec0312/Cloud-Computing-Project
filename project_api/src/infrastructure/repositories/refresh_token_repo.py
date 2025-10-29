from src.domain.entities.refresh_token import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class RefreshTokenRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, refresh_token: RefreshToken) -> None:
        self.session.add(refresh_token)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            """
            SELECT *
            FROM refresh_tokens
            WHERE token_hash = :token_hash
            """,
            {"token_hash": token_hash}
        )
        row = result.first()
        if row:
            return row[0]  # Assuming the first column is the RefreshToken entity
        return None
    
    async def revoke_active(self, user_id: str, session_id: uuid.UUID, ) -> uuid.UUID | None:
        return await self.session.execute(
            "UPDATE refresh_tokens" \
            " SET revoked_at = NOW()" \
            " WHERE user_id = :user_id" \
            " AND session_id = :session_id" \
            " AND revoked_at IS NULL" \
            " RETURNING id",
        )
    
    async def revoke_all_user_tokens(self, user_id:str) -> None:
        await self.session.execute(
            "UPDATE refresh_tokens" \
            " SET revoked_at = NOW()" \
            " WHERE user_id = :user_id" \
                    )       
        
    async def revoke_by_id(self, token_id: uuid.UUID) -> None:
        await self.session.execute(
            "UPDATE refresh_tokens" \
            " SET revoked_at = NOW()" \
            " WHERE id = :token_id" \
            " RETURNING id",
            {"token_id": token_id}
        )