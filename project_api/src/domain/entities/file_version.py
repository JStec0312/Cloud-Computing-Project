from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, TIMESTAMP, text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.file import File
    from src.domain.entities.user import User
    from src.domain.entities.blob import Blob

class FileVersion(Base):
    __tablename__ = "file_versions"
    __table_args__ = (UniqueConstraint("file_id", "version_no", name="uq_file_versions_file_ver"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    uploaded_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    blob_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("blobs.id", ondelete="CASCADE"), nullable=False)
    
    file: Mapped["File"] = relationship(back_populates="versions", uselist=False, viewonly=True, primaryjoin="File.id==FileVersion.file_id")
    current_of: Mapped[List["File"]] = relationship(back_populates="current_version", uselist=True, viewonly=True, primaryjoin="File.current_version_id==FileVersion.id")
    uploader: Mapped[Optional["User"]] = relationship(back_populates="uploaded_versions")
    blob : Mapped["Blob"] = relationship(back_populates="file_versions", uselist=False, viewonly=True, primaryjoin="Blob.id==FileVersion.blob_id")
    def __repr__(self) -> str:
        return f"FileVersion(id={self.id}, file_id={self.file_id}, version_no={self.version_no}, uploaded_by={self.uploaded_by})"
