from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import TIMESTAMP, text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base
import uuid
from src.domain.enums.op_type import OpType

if TYPE_CHECKING:
    from src.domain.entities.user import User
    from src.domain.entities.session import Session
    from src.domain.entities.file import File
    from src.domain.entities.file_version import FileVersion
    from src.domain.entities.package import Package

class LogBook(Base):
    __tablename__ = "logbook"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    occurred_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user_id: Mapped[Optional["uuid.UUID"]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[Optional["uuid.UUID"]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    op_type: Mapped[OpType] = mapped_column(SAEnum(OpType, name="op_type"), nullable=False)
    file_id: Mapped[Optional["uuid.UUID"]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    file_version_id: Mapped[Optional["uuid.UUID"]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("file_versions.id", ondelete="SET NULL"), nullable=True)
    package_id: Mapped[Optional["uuid.UUID"]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("packages.id", ondelete="SET NULL"), nullable=True)
    remote_addr: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column()
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    package_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("packages.id", ondelete="SET NULL"), nullable=True)


    user: Mapped[Optional["User"]] = relationship()
    session: Mapped[Optional["Session"]] = relationship()
    file: Mapped[Optional["File"]] = relationship()
    file_version: Mapped[Optional["FileVersion"]] = relationship()
    package: Mapped[Optional["Package"]] = relationship()
    def __repr__(self) -> str:
        return f"LogBook(id={self.id}, occurred_at={self.occurred_at}, op_type={self.op_type})"
