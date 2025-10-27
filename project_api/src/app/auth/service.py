from src.app.auth.models import RegisterUserResponse
from . import models
from sqlalchemy.ext.asyncio import AsyncSession
from src.entities.user import User
from uuid import uuid4

def register_user(data: models.RegisterUserRequest, db: AsyncSession) -> models.RegisterUserResponse:
    new_user = User(
        id =uuid4(),
        email = data.email,
        hashed_password  = data.password,
        created_at = "now()"
    )
    return new_user