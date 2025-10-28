from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.repositories.user_repo import UserRepo
from src.infrastructure.repositories.logbook_repo import LogbookRepo
from src.infrastructure.repositories.session_repo import SessionRepo
from src.infrastructure.repositories.refresh_token_repo import RefreshTokenRepo

class SqlAlchemyUoW:
    """
    Każda instancja UoW:
    - otwiera AsyncSession,
    - zaczyna transakcję w __aenter__,
    - daje dostęp do repo w ramach tej sesji,
    - commit/rollback po stronie warstwy application (use-case).
    """
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        user_repo_factory: Callable[[AsyncSession], UserRepo] = UserRepo,
        user_session_repo_factory: Callable[[AsyncSession], SessionRepo] = SessionRepo,
        logbook_repo_factory: Callable[[AsyncSession], LogbookRepo] = LogbookRepo,
        refresh_token_repo_factory: Callable[[AsyncSession], RefreshTokenRepo] = RefreshTokenRepo,

    ):
        self._session_factory = session_factory
        self._user_repo_factory = user_repo_factory
        self._logbook_repo_factory = logbook_repo_factory
        self._user_session_repo_factory = user_session_repo_factory
        self._refresh_token_repo_factory = refresh_token_repo_factory
        self.session: AsyncSession | None = None
        self.users: UserRepo | None = None
        self.logbook: LogbookRepo | None = None
        self.user_session: SessionRepo | None = None
        self.refresh_token: RefreshTokenRepo | None = None
        self._tx = None

    async def __aenter__(self) -> "SqlAlchemyUoW":
        self.session = self._session_factory()
        self.users = self._user_repo_factory(self.session)
        self.logbook = self._logbook_repo_factory(self.session)
        self.user_session=  self._user_session_repo_factory(self.session)
        self.refresh_token = self._refresh_token_repo_factory(self.session)
        self._tx = self.session.begin()
        await self._tx.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self._tx.__aexit__(exc_type, exc, tb)
        finally:
            # zamknij sesję zawsze
            await self.session.close()  # type: ignore[union-attr]

    async def commit(self) -> None:
        # flush -> commit, jeśli chcesz stricte kontrolować flush
        await self.session.flush()   # type: ignore[union-attr]
        await self.session.commit()  # type: ignore[union-attr]

    async def rollback(self) -> None:
        await self.session.rollback()  # type: ignore[union-attr]
