import os
import shutil
import aiofiles # pip install aiofiles
from pathlib import Path
from typing import BinaryIO, AsyncGenerator
from src.application.abstraction.IFileStorage import IBlobStorage

class LocalBlobStorage(IBlobStorage):
    def __init__(self, base_path: str = "./local_storage_data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, file_hash: str) -> Path:
        prefix1 = file_hash[0:2]
        prefix2 = file_hash[2:4]
        return self.base_path / prefix1 / prefix2 / file_hash

    async def save(self, file_stream: BinaryIO, file_hash: str) -> str:
        target_path = self._get_path(file_hash)
        if target_path.exists():
            return str(target_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(target_path, 'wb') as f:
            while chunk := file_stream.read(1024 * 1024): # 1MB chunks
                f.write(chunk)
        
        return str(target_path)

    async def get(self, file_hash: str) -> AsyncGenerator[bytes, None]:
        target_path = self._get_path(file_hash)
        if not target_path.exists():
            raise FileNotFoundError(f"Blob {file_hash} not found")

        async with aiofiles.open(target_path, 'rb') as f:
            while chunk := await f.read(1024 * 1024): # 1MB chunks
                yield chunk

    async def delete(self, file_hash: str) -> None:
        target_path = self._get_path(file_hash)
        if target_path.exists():
            os.remove(target_path)    
    async def exists(self, file_hash: str) -> bool:
        return self._get_path(file_hash).exists()