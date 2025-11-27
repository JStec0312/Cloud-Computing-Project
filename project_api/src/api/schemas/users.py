from pydantic import BaseModel, ConfigDict, EmailStr
import uuid

class UserFromToken(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    model_config = ConfigDict(from_attributes=True)