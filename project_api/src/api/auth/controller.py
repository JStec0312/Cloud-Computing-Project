from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.client_data import ClientData
from src.database.core import get_db
from src.rate_limiting import limiter
from . import models
from . import service
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=models.RegisterUserResponse)
@limiter.limit("5/minute")
async def register_user(request: Request, register_user_request: models.RegisterUserRequest , db:AsyncSession=Depends(get_db)):
    user = await service.register_user(register_user_request, db, client_data=ClientData(ip=request.client.host, user_agent=request.headers.get("User-Agent")))
    return user

@router.post("/login")
def login_user():
    pass

@router.post("/logout")
def logout_user():
    pass

@router.post("/logout/all")
def logout_all_user():
    pass

@router.post("/refresh")
def refresh_token():
    pass

