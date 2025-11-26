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
        # 1. Przygotowanie danych pliku
        content = await file.read()
        size_bytes = len(content)
        sha256_hash = hashlib.sha256(content).hexdigest()
        await file.seek(0)  # Reset wskaźnika, aby storage mógł zapisać plik

        async with uow:
            # 2. Logowanie próby (przed logiką biznesową)
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

            # 3. Obsługa Bloba (Deduplikacja)
            blob = await uow.blobs.get_by_hash(sha256_hash)
            is_new_blob = False

            if not blob:
                is_new_blob = True
                # Fizyczny zapis na dysk tylko jeśli blob nie istnieje
                storage_path = await self.storage.save(file, sha256_hash)
                
                blob = Blob(
                    sha256=sha256_hash,
                    size_bytes=size_bytes,
                    storage_path=storage_path,
                )
                await uow.blobs.add(blob)
                # Flush jest ważny! Nadaje ID nowemu obiektowi (jeśli baza generuje ID)
                await uow.session.flush()

            # 4. Walidacja Parent Folder (jeśli podano)
            if parent_folder_id:
                parent_folder: File = await uow.files.get(parent_folder_id)
                if not parent_folder:
                     raise InvalidParentFolder(f"Folder {parent_folder_id} not found")
                
                # Walidacja uprawnień i typu
                if parent_folder.owner_id != user_id:
                    raise InvalidParentFolder("Access denied to this folder")
                if not parent_folder.is_folder:
                    raise InvalidParentFolder("Target is not a folder")

            # 5. Tworzenie Pliku (To musi być POZA if parent_folder_id)
            new_file = File(
                owner_id=user_id,
                name=file.filename,
                mime_type=file.content_type,
                is_folder=False,
                parent_folder_id=parent_folder_id, # Może być UUID lub None
            )
            await uow.files.add(new_file)
            await uow.session.flush()  # Musimy mieć ID pliku dla FileVersion

            # 6. Tworzenie Wersji
            # Uwaga: Łączymy wersję z Blobem. Zalecam użycie blob_id (FK), 
            # ale zostawiłem Twoje pola, jeśli tak masz w modelu.
            new_version = FileVersion(
                file_id=new_file.id,
                version_no=1,         # Zakładamy wersję 1 dla nowego pliku
                uploaded_by=user_id,
                # Opcjonalnie, jeśli trzymasz te dane też w wersji (denormalizacja):
                # size_bytes=blob.size_bytes, 
            )
            await uow.file_versions.add(new_version)
            await uow.session.flush()

            # 7. Aktualizacja wskaźnika na aktualną wersję
            new_file.current_version_id = new_version.id

            # 8. Logowanie sukcesu
            await self.logbook.register_log(
                uow=uow,
                op_type=OpType.UPLOAD,
                user_id=user_id,
                remote_addr=ip,
                user_agent=user_agent,
                details={
                    "filename": new_file.name,
                    "file_id" : str(new_file.id),
                    "file_version_id": str(new_version.id),
                    "blob_id": str(blob.id),
                    "size": size_bytes,
                    "deduplicated": not is_new_blob,
                    "parent_folder": str(parent_folder_id) if parent_folder_id else "root"
                }
            )

            await uow.commit()
            
            return {
                "id": new_file.id,
                "name": new_file.name,
                "size": size_bytes,
                "deduplicated": not is_new_blob
            }

                                