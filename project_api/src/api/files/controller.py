from fastapi import APIRouter

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

@router.post("/")
async def upload_file():
    pass

@router.get("/")
async def get_user_files():
    pass

@router.patch("/{file_id}/rename")
async def rename_file():
    pass

@router.get("/{file_id}/download")
async def download_file():
    pass


@router.delete("/{file_id}")
async def delete_file():
    pass

