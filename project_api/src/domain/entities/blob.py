from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, List
from sqlalchemy import BigInteger, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.package import Package
    from src.domain.entities.file_version import FileVersion

class Blob(Base):
    __tablename__ = "blobs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    file_versions: Mapped[List["FileVersion"]] = relationship(back_populates="blob")

    packages: Mapped[List["Package"]] = relationship(back_populates="archive_blob")
    def __repr__(self) -> str:
        return f"Blob(id={self.id}, sha256={self.sha256}, size_bytes={self.size_bytes})"
