import mimetypes
import os
from fastapi import APIRouter, Depends, Header, Request, File, UploadFile, Form, Query, Cookie, HTTPException
from urllib.parse import quote

from fastapi.responses import StreamingResponse
from src.deps import get_uow
from src.api.schemas.files import  RenameFileRequest, FileResponse, VersionResponse
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.file_service import FileService
from src.deps import get_filesvc as get_file_service
from src.api.auto_auth import current_user
from typing import Annotated, Optional
from src.rate_limiting import limiter
import uuid
from src.api.schemas.users import UserFromToken
from src.application.errors import FileTooLargeError, FolderNotFoundError, InvalidParentFolder, FileNameExistsError, FileNotFoundError, AccessDeniedError, FolderNameExistsError
from src.api.schemas.files import DirectoryListingResponse, CreateFolderRequest
from uuid import UUID
from src.config.app_config import settings

router = APIRouter(
    prefix="/files",
    tags=["files"],
)
RATE_LIMIT = settings.STANDARD_RATE_LIMIT
@router.post("/", status_code=201)
@limiter.limit(RATE_LIMIT)
#/api/v1/files/?parent_id=uuid-here
async def upload_file(
    request: Request,
    parent_id: Optional[UUID] = Form(None, description="ID folderu nadrzędnego. Jeśli brak - plik zostanie przesłany do Root."),

    file: UploadFile = File(...), 
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
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except InvalidParentFolder as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    
    

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
        raise HTTPException(status_code=e.status_code, detail=str(e))
    



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
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))



@router.get("/{file_id}/download", status_code=200)
async def download_file(
    file_id: UUID,
    request: Request,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    try:
        file_meta, file_stream = await filesvc.download_file(
            uow=uow,
            user_id=current_user.id,
            file_id=file_id,
            ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        final_filename = file_meta.name
        _, ext = os.path.splitext(final_filename)
        
        if not ext:
            if hasattr(file_meta, "extension") and file_meta.extension:
                 final_filename += file_meta.extension
            
            elif file_meta.mime_type:
                 guessed_ext = mimetypes.guess_extension(file_meta.mime_type)
                 if guessed_ext:
                     final_filename += guessed_ext

        encoded_filename = quote(final_filename)
        
        headers = {
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"
        }

        media_type = file_meta.mime_type if file_meta.mime_type else "application/octet-stream"

        return StreamingResponse(file_stream, media_type=media_type, headers=headers)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) # Zmieniłem na 404
    except AccessDeniedError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.delete("/{file_id}", status_code=204)
async def delete_file(
    request: Request,
    file_id: UUID,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    """
    Usuwa plik.
    """
    try:
        await filesvc.delete_file(
            uow=uow,
            user_id=current_user.id,
            file_id=file_id,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/folders", status_code=201)
async def create_folder(
    body: CreateFolderRequest, 
    request: Request,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    try:
        folder = await filesvc.create_folder(
            uow=uow,
            user_id=current_user.id,
            folder_name=body.folder_name,
            parent_folder_id=body.parent_folder_id,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        return folder
    except FolderNameExistsError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except FolderNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except InvalidParentFolder as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))



@router.get("/{file_id}/versions", response_model=list[VersionResponse])
async def get_file_versions(
    file_id: UUID,
    request: Request,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    try:
        versions = await filesvc.get_file_versions(
            uow=uow,
            user_id=current_user.id,
            file_id=file_id,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        return versions
    except FileNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    


@router.get("/{file_id}/versions/{version_id}/download")
async def download_file_version(
    file_id: UUID,
    version_id: UUID,
    request: Request,
    current_user: UserFromToken = Depends(current_user),
    filesvc: FileService = Depends(get_file_service),
    uow: SqlAlchemyUoW = Depends(get_uow)
):
    """
    Pobiera (ściąga) konkretną wersję pliku.
    """
    pass


