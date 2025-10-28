from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.user import User
    from src.domain.entities.blob import Blob
    from src.domain.entities.package_item import PackageItem

class Package(Base):
    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    archive_blob_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("blobs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    expires_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=True))

    creator: Mapped[Optional["User"]] = relationship(back_populates="packages_created")
    archive_blob: Mapped[Optional["Blob"]] = relationship(back_populates="packages")
    items: Mapped[List["PackageItem"]] = relationship(back_populates="package", cascade="all, delete-orphan")
    def __repr__(self) -> str:
        return f"Package(id={self.id}, name={self.name}, created_by={self.created_by})"
