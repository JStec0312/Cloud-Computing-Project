from abc import ABC, abstractmethod
from typing import BinaryIO, AsyncGenerator

class IBlobStorage(ABC):
    """
    Interfejs dla systemu plików. 
    Dzięki temu Application Layer nie wie, czy pliki są na dysku C:, czy w AWS S3.
    """

    @abstractmethod
    async def save(self, file_stream: BinaryIO, file_hash: str) -> str:
        """
        Zapisuje plik. 
        Zwraca ścieżkę (lub klucz), pod którym plik został zapisany.
        """
        pass

    @abstractmethod
    async def get(self, file_hash: str) -> AsyncGenerator[bytes, None]:
        """
        Pobiera plik jako strumień bajtów.
        """
        pass

    @abstractmethod
    async def delete(self, file_hash: str) -> None:
        """
        Usuwa plik fizycznie.
        """
        pass
    
    @abstractmethod
    async def exists(self, file_hash: str) -> bool:
        """
        Sprawdza czy taki blob już fizycznie istnieje.
        """
        pass