from src.application.abstraction.IFileStorage import IBlobStorage
from src.domain.entities import file
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.logbook_service import LogbookService
from src.domain.entities.blob import Blob
import hashlib
from fastapi import UploadFile
from src.application.errors import FileTooLargeError, FolderNotFoundError, InvalidParentFolder, FileNotFoundError
from src.domain.enums.op_type import OpType
from src.domain.entities.file import File
from src.domain.entities.file_version import FileVersion
from uuid import UUID
from typing import Optional
from src.api.schemas.files import FileResponse
import fastapi
from src.config.app_config import settings
from src.application.errors import FileNameExistsError

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
        uow: SqlAlchemyUoW,
        session_id: Optional[UUID] = None
    ):
        
        content = await file.read()
        size_bytes = len(content)
        max_size_bytes = settings.max_file_upload_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            raise FileTooLargeError()
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
                parent_folder: File = await uow.files.get_by_id(parent_folder_id)
                if not parent_folder:
                     raise InvalidParentFolder(parent_folder_id, "Parent folder does not exist.")
                
                if parent_folder.owner_id != user_id:
                    raise InvalidParentFolder(parent_folder_id, "Access denied to this folder.")
                if not parent_folder.is_folder:
                    raise InvalidParentFolder(parent_folder_id, "Target is not a folder.")

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
                session_id=session_id,
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


    async def list_files(
        self, 
        uow: SqlAlchemyUoW,
        ip: str,
        user_agent: str,
        user_id: UUID, 
        folder_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> dict:
        async with uow:
            await self.logbook.register_log(
                uow=uow,
                op_type=OpType.LIST_FILES,
                user_id=user_id,
                remote_addr=ip,
                session_id=session_id,
                user_agent=user_agent,
                details={"folder_id": str(folder_id) if folder_id else "root", "status": "initiated"}
            )
            breadcrumbs = []
            
            if folder_id:
                folder = await uow.files.get_by_id(folder_id)
                if not folder or folder.owner_id != user_id or not folder.is_folder:
                    self.logbook.register_log(
                        uow=uow,
                        op_type=OpType.LIST_FILES,
                        user_id=user_id,
                        remote_addr=ip,
                        session_id=session_id,
                        user_agent=user_agent,
                        details={"folder_id": str(folder_id), "status": "failed"}
                    )
                    raise FolderNotFoundError(f"Folder {folder_id} not found or access denied")
                
                
                curr = folder
                while curr:
                    breadcrumbs.insert(0, {"id": str(curr.id), "name": curr.name})
                    if curr.parent_folder_id:
                         
                         curr = await uow.files.get_by_id(curr.parent_folder_id)
                    else:
                        curr = None
            
            
            files_db = await uow.files.list_in_folder(user_id, folder_id)

            items = []
            for f in files_db:
                size = 0
                if not f.is_folder and f.current_version and f.current_version.blob:
                    size = f.current_version.blob.size_bytes
                


                items.append({
                    "id": f.id,
                    "name": f.name,
                    "is_folder": f.is_folder,
                    "mime_type": f.mime_type,
                    "size_bytes": size,
                })

            self.logbook.register_log(
                uow=uow,
                op_type=OpType.LIST_FILES,
                session_id=session_id,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                details={"folder_id": str(folder_id) if folder_id else "root", "status": "completed"}
            )

            return {
                "current_folder_id": folder_id,
                "items": items,
                "breadcrumbs": breadcrumbs
            }
        

    async def rename_file(self, uow: SqlAlchemyUoW,  user_id: UUID,  file_id: UUID,  new_name: str, ip: str, user_agent: str, session_id: Optional[UUID] = None) -> FileResponse:
        async with uow:
            file : File = await uow.files.get_by_id(file_id)
            
            if not file or file.owner_id != user_id:
                self.logbook.register_log(
                    uow=uow,
                    op_type=OpType.RENAME,
                    user_id=user_id,
                    remote_addr=ip,
                    session_id=session_id,
                    user_agent=user_agent,
                    details={
                        "file_id": str(file_id),
                        "status": "failed",
                        "attempted_name": new_name,
                        "reason": "not_found"
                    }
                )
                raise FileNotFoundError(detail=f"File with id {file_id} not found.")

            current_size = file.current_version.blob.size_bytes if file.current_version and file.current_version.blob else 0
            if file.name == new_name:
                await self.logbook.register_log(
                    uow=uow,
                    op_type=OpType.RENAME,
                    user_id=user_id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    session_id=session_id,
                    details={
                        "file_id": str(file.id),
                        "status": "no_change",
                        "attempted_name": new_name
                    }
                )
                return FileResponse(
                    id=file.id,
                    name=file.name,
                    is_folder=file.is_folder,
                    mime_type=file.mime_type,
                    size_bytes=current_size, 
                ) 

            sibling = await uow.files.get_by_name_in_folder(
                user_id=user_id,
                name=new_name,
                parent_id=file.parent_folder_id
            )
            
            if sibling:
                await self.logbook.register_log(
                    uow=uow,
                    op_type=OpType.RENAME,
                    user_id=user_id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    session_id=session_id,
                    details={
                        "file_id": str(file.id),
                        "status": "failed",
                        "attempted_name": new_name,
                        "reason": "name_exists"
                    }
                )
                raise FileNameExistsError(detail=f"File name '{new_name}' already exists in the target folder.")

            old_name = file.name
            file.name = new_name
            await self.logbook.register_log(
                uow=uow,
                op_type=OpType.RENAME,
                user_id=user_id,
                file_id=file.id,
                remote_addr=ip,
                session_id=session_id,
                user_agent=user_agent,
                details={
                    "old_name": old_name,
                    "new_name": new_name,
                    "is_folder": file.is_folder
                }
            )
            await uow.commit() 
            
            return FileResponse(
                id=file.id,
                name=new_name, 
                is_folder=file.is_folder,
                mime_type=file.mime_type,
                size_bytes=current_size,      
            )