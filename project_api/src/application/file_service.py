from src.application.abstraction.IFileStorage import IBlobStorage
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.logbook_service import LogbookService
from src.domain.entities.blob import Blob
from src.common.utils.time_utils import utcnow
import hashlib
from src.application.errors import InvalidParentFolder
from src.domain.enums.op_type import OpType
from src.domain.entities.file import File
from src.domain.entities.file_version import FileVersion
from uuid import UUID
from typing import Optional
from fastapi import UploadFile

class FileService:
    def __init__(self, logbook: LogbookService, storage: IBlobStorage):
        self.logbook = logbook
        self.storage:IBlobStorage  = storage

    async def upload_file(
        self, 
        user_id: UUID, 
        file: UploadFile, 
        parent_folder_id: Optional[UUID], 
        ip: str, 
        user_agent: str, 
        uow: SqlAlchemyUoW
    ):
        content = await file.read()
        size_bytes = len(content)
        sha256_hash = hashlib.sha256(content).hexdigest()
        await file.seek(0) 

        async with uow:
            await self.logbook.register_log(
                uow=uow,
                op_type=OpType.FILE_UPLOAD_ATTEMPT,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                details={
                    "filename": file.filename,
                    "size": size_bytes,
                    "sha256": sha256_hash
                }
            )

            blob = await uow.blobs.get_by_hash(sha256_hash)
            is_new_blob = False

            if not blob:
                is_new_blob = True
                storage_path = await self.storage.save(file, sha256_hash)
                
                blob = Blob(
                    sha256=sha256_hash,
                    size_bytes=size_bytes,
                    storage_path=storage_path,
                )
                await uow.blobs.add(blob)
                await uow.session.flush()

            if parent_folder_id:
                parent_folder: File = await uow.files.get(parent_folder_id)
                if not parent_folder:
                     raise InvalidParentFolder(f"Folder {parent_folder_id} not found")
                
                if parent_folder.owner_id != user_id:
                    raise InvalidParentFolder("Access denied to this folder")
                if not parent_folder.is_folder:
                    raise InvalidParentFolder("Target is not a folder")

            existing_file = await uow.files.get_by_owner_and_name(
                owner_id=user_id, 
                name=file.filename, 
                parent_id=parent_folder_id
            )

            target_file_id = None
            new_version_no = 1

            if existing_file:
                target_file_id = existing_file.id
                if existing_file.current_version:
                    new_version_no = existing_file.current_version.version_no + 1
                else:
                    new_version_no = 1 
                
                existing_file.mime_type = file.content_type
                
            else:
                new_file = File(
                    owner_id=user_id,
                    name=file.filename,
                    mime_type=file.content_type,
                    is_folder=False,
                    parent_folder_id=parent_folder_id,
                )
                await uow.files.add(new_file)
                await uow.session.flush() 
                target_file_id = new_file.id
                new_version_no = 1
                existing_file = new_file 

            new_version = FileVersion(
                file_id=target_file_id,
                version_no=new_version_no,
                uploaded_by=user_id,
                blob_id=blob.id, 
                created_at=utcnow()
            )
            await uow.file_versions.add(new_version)
            await uow.session.flush()

            existing_file.current_version_id = new_version.id

            await self.logbook.register_log(
                uow=uow,
                op_type=OpType.UPLOAD,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                details={
                    "filename": file.filename,
                    "file_id": str(target_file_id),
                    "version_no": new_version_no,
                    "deduplicated": not is_new_blob
                }
            )
            await uow.commit()

            return {
                "id": target_file_id,
                "name": file.filename,
                "version": new_version_no, # Zwracamy numer wersji
                "deduplicated": not is_new_blob
            }

                                