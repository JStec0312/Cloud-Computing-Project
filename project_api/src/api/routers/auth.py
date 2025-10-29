from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import logging
from src.api.deps import get_uow, get_auth_service
from src.application.errors import (InvalidCredentialsError, RefreshTokenError,
    RefreshTokenMissingError, UserAlreadyExistsError, UserNotFoundError)
from src.application.auth_service import AuthService
from src.infrastructure.uow import SqlAlchemyUoW
from src.api.schemas.auth import LoginUserRequest, RefreshTokenResponse
from src.config.app_config import settings
from ..schemas.auth import LoginUserResponse, RegisterUserRequest, RegisterUserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=RegisterUserResponse, status_code=status.HTTP_201_CREATED)
async def register_user_ep(
    body: RegisterUserRequest,
    request: Request,
    uow: SqlAlchemyUoW = Depends(get_uow),
    auth: AuthService = Depends(get_auth_service),
):
    try:
        user = await auth.register_user(
            uow,
            email=body.email,
            display_name=body.display_name,
            password=body.password,
            ip=request.client.host,
            user_agent=request.headers.get("User-Agent", ""),
        )
        return RegisterUserResponse(
            id=user.id,
            display_name=user.display_name,
            email=user.email,
            created_at=user.created_at,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
@router.post("/login", response_model=LoginUserResponse, status_code=status.HTTP_200_OK)
async def login_user_ep(
    body: LoginUserRequest,
    request: Request,
    response: Response,
    uow: SqlAlchemyUoW = Depends(get_uow),
    auth: AuthService = Depends(get_auth_service),
):
    try:
        user, access_token, refresh_token = await auth.authenticate_user(
            uow,
            email=body.email,
            password=body.password,
            ip=request.client.host,
            user_agent=request.headers.get("User-Agent", ""),
        )
        response.set_cookie(settings.refresh_cookie_name, refresh_token, httponly=settings.httponly_cookie, secure=settings.secure_cookie, samesite=settings.samesite_cookie)
        return LoginUserResponse(
            access_token=access_token,
            user=RegisterUserResponse(
                id=user.id,
                display_name=user.display_name,
                email=user.email,
            ),
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    

@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token_ep(
    request: Request,
    response: Response,
    uow: SqlAlchemyUoW = Depends(get_uow),
    auth: AuthService = Depends(get_auth_service),
):
    try:
        refresh_token_cookie = request.cookies.get(settings.refresh_cookie_name)
        if not refresh_token_cookie:
            raise RefreshTokenMissingError(detail="Refresh token cookie is missing")
        user, access_token, new_refresh_token = await auth.refresh_tokens(
            uow,
            token_hash=refresh_token_cookie,
            ip=request.client.host,
            user_agent=request.headers.get("User-Agent", ""),
        )
        response.set_cookie(settings.refresh_cookie_name, new_refresh_token, httponly=settings.httponly_cookie, secure=settings.secure_cookie, samesite=settings.samesite_cookie)
        return RefreshTokenResponse(
            access_token=access_token,
            user=RegisterUserResponse(
                id=user.id,
                display_name=user.display_name,
                email=user.email,
            ),
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RefreshTokenError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except RefreshTokenMissingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

