from fastapi import APIRouter, Depends, Header, Request, File, UploadFile, Form
from src.deps import get_uow
from src.api.schemas.files import UploadFileRequest
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.file_service import FileService
from src.deps import get_filesvc as get_file_service
from src.api.auto_auth import current_user
from typing import Annotated, Optional
import uuid
from src.api.schemas.users import UserFromToken

router = APIRouter(
    prefix="/files",
    tags=["files"],
)
@router.post("/", status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...), 
    parent_id: Optional[uuid.UUID] = Form(None), 
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow) 
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return await filesvc.upload_file(
        uow=uow,
        user_id = current_user.id,
        file = file,
        parent_folder_id = parent_id,
        ip = ip,
        user_agent = user_agent
    )

@router.get("/")
async def get_user_files(current_user = Depends(current_user)):
    return {"message": f"Files for user {current_user.id}"}

@router.patch("/{file_id}/rename")
async def rename_file():
    pass

@router.get("/{file_id}/download")
async def download_file():
    pass


@router.delete("/{file_id}")
async def delete_file():
    pass

