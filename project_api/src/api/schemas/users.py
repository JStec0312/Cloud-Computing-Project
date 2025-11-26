from pydantic import BaseModel, ConfigDict, EmailStr

class UserFromToken(BaseModel):
    id: int
    email: str
    display_name: str
    model_config = ConfigDict(from_attributes=True)