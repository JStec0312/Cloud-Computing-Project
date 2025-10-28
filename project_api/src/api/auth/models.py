# models.py (schematy)
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

class RegisterUserRequest(BaseModel):
    display_name: str
    email: EmailStr
    password: str

class RegisterUserResponse(BaseModel):
    display_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
    id: UUID
