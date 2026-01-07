# src/api/deps.py  (uzupełnienie)
from fastapi import Depends
from src.application.refresh_token_service import RefreshTokenService
from src.application.session_service import SessionService
from src.infrastructure.db.session import async_session_maker
from src.infrastructure.security.token_hasher import TokenHasher
from src.infrastructure.uow import SqlAlchemyUoW
from src.infrastructure.security.password import PasswordHasher
from src.application.auth_service import AuthService
from src.application.logbook_service import LogbookService
from src.application.file_service import FileService
from src.config.app_config import settings
from src.infrastructure.storage.S3BlobStorage import S3BlobStorage



async def get_uow():
    return SqlAlchemyUoW(async_session_maker)

def get_hasher():
    return PasswordHasher()

def get_logsvc():
    return LogbookService()

def get_token_hasher():
    return TokenHasher(settings.token_pepper)


def get_refresh_token_svc(hasher: TokenHasher = Depends(get_token_hasher)):
    return RefreshTokenService(
        hasher=hasher
    )


def get_session_svc():
    return SessionService()

def get_auth_service(
    hasher: PasswordHasher = Depends(get_hasher),
    logsvc: LogbookService = Depends(get_logsvc),
    refresh_token_svc: RefreshTokenService = Depends(get_refresh_token_svc),
    session_svc: SessionService = Depends(get_session_svc),
    token_hasher: TokenHasher = Depends(get_token_hasher)
):
    return AuthService(hasher, logsvc, refresh_token_svc, session_svc, token_hasher)

def get_storage():
    if settings.storage_type == "s3":
        return S3BlobStorage(
            bucket=settings.s3_bucket,
            region=settings.s3_region
        )

def get_filesvc(logsvc: LogbookService = Depends(get_logsvc), storage = Depends(get_storage)):
    return FileService(logsvc, storage)
