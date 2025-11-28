from pydantic import BaseModel, ConfigDict, Field  
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class UploadFileRequest(BaseModel):
    filename:str
    content_type: str
    size: int
    file: bytes

class FileResponse(BaseModel):
    id: UUID
    name: str
    is_folder: bool
    mime_type: Optional[str] = None
    size_bytes: int = 0

    model_config = ConfigDict(from_attributes=True)

class DirectoryListingResponse(BaseModel):
    """
    Odpowiedź zawierająca listę plików ORAZ ścieżkę (breadcrumbs),
    żeby frontend wiedział gdzie jest (np. Home > Dokumenty > Praca).
    """
    current_folder_id: Optional[UUID]
    items: List[FileResponse]
    breadcrumbs: List[dict] # np. [{"i

class VersionResponse(BaseModel):
    id: UUID
    version_no: int
    uploaded_at: datetime
    uploaded_by: UUID
    size_bytes: int
    model_config = ConfigDict(from_attributes=True) 


class RenameFileRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=255, description="Nowa nazwa pliku (z rozszerzeniem!)")