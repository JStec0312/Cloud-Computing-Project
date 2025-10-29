from pydantic import BaseModel, ConfigDict  

class UploadFileRequest(BaseModel):
    filename:str
    content_type: str
    size: int
    file: bytes