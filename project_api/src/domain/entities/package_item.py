from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.package import Package
    from src.domain.entities.file import File
    from src.domain.entities.file_version import FileVersion

class PackageItem(Base):
    __tablename__ = "package_items"
    __table_args__ = (UniqueConstraint("package_id", "file_id", "version_id", name="uq_package_item"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("file_versions.id", ondelete="CASCADE"), nullable=False)
    path_in_archive: Mapped[Optional[str]] = mapped_column(Text)

    package: Mapped["Package"] = relationship(back_populates="items")
    file: Mapped["File"] = relationship()
    version: Mapped["FileVersion"] = relationship(back_populates="package_items")
    def __repr__(self) -> str:
        return f"PackageItem(id={self.id}, package_id={self.package_id}, file_id={self.file_id}, version_id={self.version_id})"
