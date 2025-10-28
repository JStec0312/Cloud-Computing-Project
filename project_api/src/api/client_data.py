from pydantic import BaseModel, ConfigDict

class ClientData(BaseModel):
    ip: str
    user_agent: str