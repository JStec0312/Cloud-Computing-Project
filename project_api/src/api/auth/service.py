import logging

from sqlalchemy.exc import IntegrityError
from src.exceptions import UserAlreadyExistsError
from . import models
from sqlalchemy.ext.asyncio import AsyncSession
from src.entities.user import User
from src.entities.logbook import LogBook
from uuid import uuid4
from passlib.context import CryptContext
from fastapi.concurrency import run_in_threadpool
from src.enums.op_type import OpType
from src.api.client_data import ClientData
logger = logging.getLogger(__name__)

password_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def hash_password(password: str) -> str:
    return await run_in_threadpool(password_context.hash, password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(password_context.verify, plain_password, hashed_password)



async def register_user(data: models.RegisterUserRequest, db: AsyncSession, client_data:ClientData ) -> models.RegisterUserResponse:
    hashed_password = await hash_password(data.password)
    new_user = User(
        id=uuid4(),
        display_name=data.display_name,
        email=data.email,
        hashed_password=hashed_password
    )
    logbook_register = LogBook(
        user_id=new_user.id,
        op_type=OpType.USER_REGISTER.value,
        remote_addr=client_data.ip,
        user_agent=client_data.user_agent,
        details = {
            "email": data.email,
            "display_name": data.display_name,
            "success": True 
        }
    )

    try:
        async with db.begin():
            db.add(new_user)
            db.add(logbook_register)


    except IntegrityError:
        logger.warning(f"Attempt to register already existing user with email: {data.email}")
        logbook_register.details["success"] = False
        logbook_register.details["error"] = "User already exists"
        async with db.begin():
            db.add(logbook_register)
        raise UserAlreadyExistsError(email=data.email)

    except Exception as e:
        logger.error(f"Error registering user: {e}")
        logbook_register.details["success"] = False
        logbook_register.details["error"] = str(e)
        async with db.begin():
            db.add(logbook_register)
        raise e
    

    
    return new_user