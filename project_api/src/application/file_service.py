import os
from src.application.abstraction.IFileStorage import IBlobStorage
from src.infrastructure.uow import SqlAlchemyUoW
from src.application.logbook_service import LogbookService
from src.domain.entities.blob import Blob
import hashlib
from fastapi import UploadFile
from src.application.errors import FileTooLargeError, FolderNameExistsError, FolderNotFoundError, InvalidParentFolder, FileNotFoundError, AccessDeniedError
from src.domain.enums.op_type import OpType
from src.domain.entities.file import File
from src.domain.entities.file_version import FileVersion
from uuid import UUID, uuid4
from src.api.schemas.files import VersionResponse
import zipfile
import mimetypes
from pathlib import Path
from typing import Optional
from src.api.schemas.files import FileResponse
from src.config.app_config import settings
import logging
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
        
        sha256 = hashlib.sha256()
        size_bytes = 0
        max_size_bytes = settings.max_file_upload_size_mb * 1024 * 1024
        
        # Czytamy plik w kawałkach po 1MB
        while chunk := await file.read(1024 * 1024):
            sha256.update(chunk)
            size_bytes += len(chunk)
            if size_bytes > max_size_bytes:
                raise FileTooLargeError()

        sha256_hash = sha256.hexdigest()
        await file.seek(0)
        mime_type = file.content_type
        _, extension = os.path.splitext(file.filename)
        extension = extension.lower() if extension else ''

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
                existing_file.extension = extension
                existing_file.mime_type = file.content_type
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
                    extension=extension,
                    is_folder=False,
                    parent_folder_id=parent_folder_id,
                )
                await uow.files.add(new_file)
                await uow.session.flush() 
                target_file_id = new_file.id
                new_version_no = 1
                existing_file = new_file 
            from src.common.utils.time_utils import utcnow
            new_version = FileVersion(
                file_id=target_file_id,
                version_no=new_version_no,
                uploaded_by=user_id,
                uploaded_at=utcnow(),
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
            
            return FileResponse(
                id=file.id,
                name=new_name, 
                is_folder=file.is_folder,
                mime_type=file.mime_type,
                size_bytes=current_size,      
            )
        
    async def delete_file(self, uow: SqlAlchemyUoW, user_id: UUID, file_id: UUID, ip: str, user_agent: str, session_id: Optional[UUID] = None):
        async with uow:
            self.logbook.register_log(
                uow=uow,
                op_type=OpType.FILE_DELETE,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                session_id=session_id,
                details={
                    "file_id": str(file_id),
                    "status": "initiated"
                }
            )
            file: File = await uow.files.get_by_id(file_id)
            if not file:
                raise FileNotFoundError(detail=f"File with id {file_id} not found.")
            if file.owner_id != user_id:
                raise AccessDeniedError(detail="Access denied to delete this file.")
            
            await uow.files.delete(file)
            self.logbook.register_log(
                uow=uow,
                op_type=OpType.FILE_DELETE,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                session_id=session_id,
                details={
                    "file_id": str(file_id),
                    "status": "completed"
                }
            )
            return
        
    async def get_file_versions(self, uow: SqlAlchemyUoW, file_id: UUID, user_id: UUID, ip: str, user_agent: str, session_id: Optional[UUID] = None) -> list[VersionResponse]:
        async with uow:
            self.logbook.register_log(
            uow=uow,
                op_type=OpType.VIEW_FILE_VERSIONS,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                session_id=session_id,
                details={
                    "file_id": str(file_id),
                    "status": "initiated"
                }
            )
            file = await uow.files.get_by_id(file_id)
            if not file:
                raise FileNotFoundError(detail=f"File with id {file_id} not found.")
            if file.owner_id != user_id:
                raise AccessDeniedError(detail="Access denied to view this file's versions.")
            
            versions = await uow.file_versions.list_by_file_id(file_id)
            self.logbook.register_log(
                uow=uow,
                op_type=OpType.LIST_FILES,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                session_id=session_id,
                details={
                    "file_id": str(file_id),
                    "status": "completed",
                    "version_count": len(versions),
                    "operation": "view_versions"
                }
            )
            
            res = []
            for v in versions:
                size_bytes = v.blob.size_bytes if v.blob else 0

                res.append(VersionResponse(
                    id=v.id,
                    version_no=v.version_no,
                    uploaded_at=v.uploaded_at,
                    uploaded_by=v.uploaded_by,
                    size_bytes=size_bytes,
                ))        
        
        return res
    
    async def create_folder(
        self,
        uow: SqlAlchemyUoW,
        user_id: UUID,
        folder_name: str,
        parent_folder_id: Optional[UUID],
        ip: str,
        user_agent: str,
        session_id: Optional[UUID] = None
    ):
        async with uow:
            self.logbook.register_log(
                uow=uow,
                op_type=OpType.FOLDER_CREATE, #TODO: add to OpType
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                session_id=session_id,
                details={
                    "folder_name": folder_name,
                    "parent_folder_id": str(parent_folder_id) if parent_folder_id else "root",
                    "status": "initiated"
                }
            )
            if parent_folder_id:
                found_parent_folder: File = await uow.files.get_by_id(parent_folder_id)
                    
                if not found_parent_folder:
                    raise FolderNotFoundError(f"Parent folder with id {parent_folder_id} not found.")
                if found_parent_folder.owner_id != user_id:
                    raise AccessDeniedError("Access denied to this folder.")
                if not found_parent_folder.is_folder:
                    raise InvalidParentFolder(parent_folder_id, "Target is not a folder.")
            
        
            existing_duplicate = await uow.files.get_by_name_and_parent(
                owner_id=user_id,
                name=folder_name,
                parent_folder_id=parent_folder_id
            )
            if existing_duplicate:
                raise FolderNameExistsError(f"Folder name '{folder_name}' already exists in the target folder.")
            new_folder = File(
                owner_id=user_id,
                name=folder_name,
                mime_type="inode/directory",
                is_folder=True,
                parent_folder_id=parent_folder_id,
            )
            await uow.files.add(new_folder)
            self.logbook.register_log(
                uow=uow,
                op_type=OpType.FOLDER_CREATE,
                user_id=user_id,
                remote_addr=ip,     
                user_agent=user_agent,
                details={
                    "folder_id": str(new_folder.id),
                    "folder_name": folder_name,
                    "parent_folder_id": str(parent_folder_id) if parent_folder_id else "root",
                    "status": "completed"
                }
            )
            return new_folder   
        
    async def download_file(
            self,
            uow: SqlAlchemyUoW,
            user_id: UUID,
            file_id: UUID,
            ip: str,
            user_agent: str,
            version_id: Optional[UUID] = None, # Przesunąłem na koniec jako opcjonalny
            session_id: Optional[UUID] = None
        ):
            async with uow:
                file_record = await uow.files.get_by_id(file_id)
                if not file_record:
                    raise FileNotFoundError(detail=f"File with id {file_id} not found.")
                if file_record.owner_id != user_id:
                    raise AccessDeniedError(detail="Access denied.")
                
                target_version = None
                if version_id:
                    version = await uow.file_versions.get_by_id(version_id)
                    if not version or version.file_id != file_record.id:
                        raise FileNotFoundError(detail=f"Version {version_id} not found for this file.")
                    target_version = version
                else:
                    if not file_record.current_version:
                        raise FileNotFoundError(detail="File has no current version.")
                    target_version = file_record.current_version

                if not target_version.blob:
                    raise FileNotFoundError(detail="Target version has no content (blob).")

                await self.logbook.register_log(
                    uow=uow,
                    op_type=OpType.DOWNLOAD,
                    user_id=user_id,
                    remote_addr=ip,
                    user_agent=user_agent,
                    session_id=session_id,
                    details={
                        "file_id": str(file_id),
                        "version_id": str(target_version.id),
                        "version_no": target_version.version_no
                    }
                )

                try:
                    file_stream = self.storage.get(target_version.blob.sha256)
                except FileNotFoundError:
                    raise FileNotFoundError(detail="Blob not found in storage.")
                return file_record, target_version, file_stream
            
    async def upload_zip_folder(
            self, 
            uow: SqlAlchemyUoW, 
            user_id: UUID, 
            file: UploadFile, 
            parent_folder_id: Optional[UUID],
            ip: str, 
            user_agent: str
        ):
        MAX_ZIP_SIZE_MB = settings.max_file_upload_size_mb
        processed_paths = set()
        folder_map = {"": parent_folder_id}
        created_files_count = 0


        try:
            exists = await uow.files.get_by_name_and_parent(
                owner_id=user_id,
                name=file.filename,
                parent_folder_id=parent_folder_id
            )
            if exists:
                raise FileNameExistsError(detail=f"An item named '{file.filename}' already exists in the target folder.")

            with zipfile.ZipFile(file.file, 'r') as zip_ref:
                zip_contents = sorted(zip_ref.infolist(), key=lambda x: x.filename)
                total_uncompressed_size = sum(zinfo.file_size for zinfo in zip_ref.infolist())
                if total_uncompressed_size > MAX_ZIP_SIZE_MB * 1024 * 1024:
                    raise FileTooLargeError(detail=f"Total uncompressed size of zip contents exceeds the limit of {MAX_ZIP_SIZE_MB} MB.")
                async with uow:
                    for member in zip_contents:
                        filename = member.filename
                        if filename in processed_paths:
                            continue
                        processed_paths.add(filename)
                        # Zip slip vulnerability check
                        if filename.startswith("/") or ".." in filename:
                            continue
                        
                        if "__MACOSX" in filename or ".DS_Store" in filename:
                            continue

                        path_parts = filename.rstrip("/").split("/") # podział na części ścieżki /wakacje/zdjecie.jpg -> ["wakacje", "zdjecie.jpg"]

                        if member.is_dir():
                            current_path_str = filename.rstrip("/") 
                            parent_path_str = "/".join(path_parts[:-1]) # Ścieżka rodzica
                            folder_name = path_parts[-1] # Nazwa bieżącego folderu
                            # Znajdź ID folderu rodzica
                            parent_db_id = folder_map.get(parent_path_str, parent_folder_id)
                            folder_uuid = await self._get_or_create_folder(
                                uow, user_id, folder_name, parent_db_id
                            )
                            
                            folder_map[current_path_str] = folder_uuid

                        else:
                            # TO JEST PLIK
                            file_name = path_parts[-1]
                            parent_path_str = "/".join(path_parts[:-1])
                            
                            # Znajdź folder rodzica
                            parent_db_id = folder_map.get(parent_path_str)
                            
                            if parent_db_id is None:
                                parent_db_id = parent_folder_id
                            with zip_ref.open(member) as source_stream:
                                ext = os.path.splitext(file_name)[1].lower()
                                mime = mimetypes.types_map.get(ext, "application/octet-stream")

                                await self._save_zip_member_as_file(
                                    uow, user_id, source_stream, file_name, 
                                    parent_db_id, mime, ext, ip, user_agent
                                )
                                created_files_count += 1

                    await uow.commit()

        except zipfile.BadZipFile as e:
            raise zipfile.BadZipFile()

        return {"status": "success", "imported_files": created_files_count}


    async def _get_or_create_folder(self, uow:SqlAlchemyUoW, user_id, name, parent_id) -> UUID:
        """Sprawdza czy folder istnieje, jak nie to tworzy."""
        existing = await uow.files.get_by_owner_and_name(
            owner_id=user_id,
            name=name,
            parent_id=parent_id
        )
        
        if existing and existing.is_folder:
            return existing.id
        
        new_folder = File(
            id = uuid4(),
            owner_id=user_id,
            name=name,
            is_folder=True,
            parent_folder_id=parent_id,
            mime_type="application/directory" ,
        )
        await uow.files.add(new_folder) 
        return new_folder.id

    async def _save_zip_member_as_file(
        self, uow: SqlAlchemyUoW, user_id, stream, filename, parent_id, mime, ext, ip, user_agent
    ):
        import hashlib
        import io
        sha256 = hashlib.sha256()
        size_bytes = 0
        content_chunks = []
        
        while chunk := stream.read(1024 * 1024):
            sha256.update(chunk)
            size_bytes += len(chunk)
            content_chunks.append(chunk)
            
        sha256_hash = sha256.hexdigest()

        blob = await uow.blobs.get_by_hash(sha256_hash)
        
        if not blob:
            full_content = b"".join(content_chunks)
            file_obj = io.BytesIO(full_content)
            
            storage_path = await self.storage.save(file_obj, sha256_hash)
            
            blob = Blob(
                id=uuid4(),  
                sha256=sha256_hash,
                size_bytes=size_bytes,
                storage_path=storage_path
            )
            await uow.blobs.add(blob)

        existing_file = await uow.files.get_by_owner_and_name(user_id, filename, parent_id)
        
        if existing_file:
            existing_file.extension = ext
            existing_file.mime_type = mime
            max_ver = await uow.file_versions.get_highest_version_no(existing_file.id)
            new_version_no = (max_ver if max_ver is not None else 0) + 1
            
            ver = FileVersion(
                file_id=existing_file.id,
                version_no=new_version_no,
                uploaded_by=user_id,
                blob_id=blob.id
            )
            await uow.file_versions.add(ver)
            
        else:
            # TWORZENIE NOWEGO PLIKU
            new_file = File(
                id=uuid4(),
                owner_id=user_id,
                name=filename,
                mime_type=mime,
                extension=ext,
                is_folder=False,
                parent_folder_id=parent_id,
                size_bytes=size_bytes
            )
            await uow.files.add(new_file)            
            ver = FileVersion(
                file_id=new_file.id,
                version_no=1,
                uploaded_by=user_id,
                blob_id=blob.id,
                size_bytes=size_bytes
            )
            await uow.file_versions.add(ver)