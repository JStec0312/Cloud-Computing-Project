from fastapi import APIRouter

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("/")
async def upload_package():
    pass

@router.patch("/{package_id}/rename")
async def rename_package():
    pass


@router.get("/")
async def get_user_packages():
    pass

@router.get("/{package_id}/download")
async def download_package():
    pass

@router.delete("/{package_id}")
async def delete_package():
    pass

