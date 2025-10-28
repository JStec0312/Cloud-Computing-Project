from src.domain.entities.refresh_token import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession

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
        