from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.core import Base

if TYPE_CHECKING:
    from src.entities.file_version import FileVersion
    from src.entities.user import User

class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255))
    current_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("file_versions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=False), nullable=False, server_default=text("now()"))

    owner: Mapped[Optional["User"]] = relationship(back_populates="owned_files")
    versions: Mapped[List["FileVersion"]] = relationship(back_populates="file", cascade="all, delete-orphan", foreign_keys="FileVersion.file_id", primaryjoin="File.id==FileVersion.file_id")
    current_version: Mapped[Optional["FileVersion"]] = relationship(foreign_keys="File.current_version_id", primaryjoin="File.current_version_id==FileVersion.id", post_update=True)
    def __repr__(self) -> str:
        return f"File(id={self.id}, name={self.name}, owner_id={self.owner_id})"
