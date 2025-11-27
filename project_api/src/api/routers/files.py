from fastapi import APIRouter, Depends, Header, Request, File, UploadFile, Form, Query, Cookie
from src.deps import get_uow
from src.api.schemas.files import  RenameFileRequest, FileResponse
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.file_service import FileService
from src.deps import get_filesvc as get_file_service
from src.api.auto_auth import current_user
from typing import Annotated, Optional
from src.rate_limiting import limiter
import uuid
from src.api.schemas.users import UserFromToken
from src.application.errors import FileTooLargeError, FolderNotFoundError, InvalidParentFolder, FileNameExistsError
from src.api.schemas.files import DirectoryListingResponse
from uuid import UUID
from src.config.app_config import settings

router = APIRouter(
    prefix="/files",
    tags=["files"],
)
RATE_LIMIT = settings.STANDARD_RATE_LIMIT
@router.post("/", status_code=201)
@limiter.limit(RATE_LIMIT)
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
    try:
        return await filesvc.upload_file(
        uow=uow,
        user_id = current_user.id,
        file = file,
        parent_folder_id = parent_id,
        ip = ip,
        user_agent = user_agent,
        )
    except FileTooLargeError as e:
        return {"error": str(e)}
    except InvalidParentFolder as e:
        return {"error": str(e)}
    
    

@router.get("/", response_model=DirectoryListingResponse)
@limiter.limit(RATE_LIMIT)
async def get_user_files(
    request: Request,
    folder_id: Optional[UUID] = Query(
        None, 
        description="ID folderu. Jeśli brak - wyświetla Root."
    ),
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    """
    Pobiera zawartość folderu (pliki i podfoldery).
    """
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    try:
        result = await filesvc.list_files(
            uow=uow,
            user_id=current_user.id, 
            folder_id=folder_id,
            ip=ip,
            user_agent=user_agent,
        )

        return result
    except FolderNotFoundError as e:
        return {"error": str(e)}
    



@router.patch("/{file_id}/rename", response_model=FileResponse)
async def rename_file(
    file_id: UUID,
    body: RenameFileRequest,
    request: Request,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)

):                               
    try:
        res =  await filesvc.rename_file(
        uow=uow,
        user_id=current_user.id,
        file_id=file_id,
        new_name=body.new_name,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
        return res
    except FileNameExistsError as e:
        return {"error": str(e)}
    except FileNotFoundError as e:
        return {"error": str(e)}


@router.get("/{file_id}/download")
async def download_file():
    pass


@router.delete("/{file_id}")
async def delete_file():
    pass

