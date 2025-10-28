# src/api/deps.py  (uzupełnienie)
from fastapi import Depends
from src.application.refresh_token_service import RefreshTokenService
from src.application.session_service import SessionService
from src.infrastructure.db.session import async_session_maker
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.security.password import PasswordHasher
from src.application.auth_service import AuthService
from src.application.logbook_service import LogbookService

async def get_uow():
    return SqlAlchemyUoW(async_session_maker)

def get_hasher():
    return PasswordHasher()

def get_logsvc():
    return LogbookService()

def get_refresh_token_svc():
    return RefreshTokenService()

def get_session_svc():
    return SessionService()

def get_auth_service(
    hasher: PasswordHasher = Depends(get_hasher),
    logsvc: LogbookService = Depends(get_logsvc),
    refresh_token_svc: RefreshTokenService = Depends(get_refresh_token_svc),
    session_svc: SessionService = Depends(get_session_svc),
):
    return AuthService(hasher, logsvc, refresh_token_svc, session_svc)


