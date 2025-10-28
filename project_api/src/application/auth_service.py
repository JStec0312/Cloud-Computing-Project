# src/application/auth_service.py
import jose
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.security.password import PasswordHasher
from src.application.errors import (InvalidCredentialsError, UserAlreadyExistsError,
    UserNotFoundError)
from src.application.logbook_service import LogbookService
from src.application.refresh_token_service import RefreshTokenService
from src.application.session_service import SessionService
from src.domain.entities import User
from src.domain.enums.op_type import OpType
from src.infrastructure.security.access_token import create_access_token, decode_access_token
from src.config.app_config import settings
from src.config.app_config import Settings

class AuthService:
    def __init__(self, hasher: PasswordHasher, logsvc: LogbookService | None = None, refresh_token_svc: RefreshTokenService | None = None, session_svc: SessionService | None = None):
        self._hasher = hasher
        self._logsvc: LogbookService | None = logsvc
        self._refresh_token_svc: RefreshTokenService | None= refresh_token_svc
        self._session_svc: SessionService | None = session_svc

    async def register_user(
        self,
        uow: SqlAlchemyUoW,
        *,
        email: str,
        display_name: str,
        password: str,
        ip: str,
        user_agent: str,
    ) -> User:
        email_norm = email.strip().lower()
        hashed = await self._hasher.hash(password)
        user = User(
            id=uuid4(),
            email=email_norm,
            display_name=display_name,
            hashed_password=hashed,
        )

        try:
            async with uow:
                await uow.users.add(user)
                await self._logsvc.register_log(
                    uow,
                    op_type=OpType.USER_REGISTER,
                    user_id=user.id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    details={"email": email_norm, "display_name": display_name, "success": True},
                )
                await uow.commit()
            return user

        except IntegrityError:
            async with uow:
                await self._logsvc.register_log(
                    uow,
                    op_type=OpType.USER_REGISTER,
                    user_id=user.id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    details={"email": email_norm, "display_name": display_name, "success": False, "error": "User already exists"},
                )
                await uow.commit()
            raise UserAlreadyExistsError(email_norm)

    async def authenticate_user(
        self,
        uow: SqlAlchemyUoW,
        *,
        email: str,
        password: str,
        ip: str,
        user_agent: str,
    ) -> tuple[User | None, str | None, str | None]:
        email_norm = email.strip().lower()
        async with uow:
            user = await uow.users.get_by_email(email_norm)
            if not user:
                await self._logsvc.register_log(
                    uow,
                    op_type=OpType.LOGIN,
                    user_id=None,
                    remote_addr=ip,
                    user_agent=user_agent,
                    details={"email": email_norm, "success": False, "error": "User not found"},
                )
                await uow.commit()
                raise UserNotFoundError(email_norm)
            if not await self._hasher.verify(password, user.hashed_password):
                await self._logsvc.register_log(
                    uow,
                    op_type=OpType.LOGIN,
                    user_id=user.id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    details={"email": email_norm, "success": False, "error": "Invalid credentials"},
                )
                await uow.commit()
                raise InvalidCredentialsError()

        access_token = create_access_token(user_id=user.id, refresh=False)
        refresh_token = create_access_token(user_id=user.id, refresh=True)
        refresh_token_hashed = await self._hasher.hash(refresh_token)
        try:
            async with uow:
                await self._logsvc.register_log(
                    uow,
                    op_type=OpType.LOGIN,
                    user_id=user.id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    details={"email": email_norm, "success": True},
                )
                session = await self._session_svc.create_session(
                    uow,
                    user_id=user.id,
                    ip=ip,
                    user_agent=user_agent,
                )
                from src.common.utils.time_utils import timedelta_days
                await self._refresh_token_svc.create_refresh_token(
                    uow,
                    user_id=user.id,
                    session_id=session.id,
                    token_hash=refresh_token_hashed,
                    revoked_id=None,
                    expires_at= timedelta_days(settings.jwt_refresh_expiration_days)
                )
                await uow.commit()
        except Exception as e:
            await uow.rollback()
            raise e

        return user, access_token, refresh_token
