# models.py (schematy)
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class RegisterUserRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
