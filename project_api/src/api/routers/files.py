from fastapi import APIRouter, Depends, Header, Request
from src.api.deps import get_uow
from src.api.schemas.files import UploadFileRequest
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.file_service import FileService
from src.api.deps import get_filesvc as get_file_service
from src.api.auto_auth import current_user
from typing import Annotated

router = APIRouter(
    prefix="/files",
    tags=["files"],
)
@router.post("/", status_code=201)
async def upload_file(
    body: UploadFileRequest,
    request: Request,
    uow: SqlAlchemyUoW = Depends(get_uow),
    filesvc: FileService = Depends(get_file_service),
):
    return filesvc.do_something(body, request)

@router.get("/")
async def get_user_files(current_user = Depends(current_user), x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None
 ):
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

