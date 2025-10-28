# src/api/auth/controller.py (skrót)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.api.deps import get_uow, get_auth_service
from src.application.errors import (InvalidCredentialsError, UserAlreadyExistsError,
    UserNotFoundError)
from src.application.auth_service import AuthService
from src.infrastructure.uow import SqlAlchemyUoW
from src.api.schemas.auth import LoginUserRequest
from ..schemas.auth import LoginUserResponse, RegisterUserRequest, RegisterUserResponse

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
        return LoginUserResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    
    