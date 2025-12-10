from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.session import Session
    from src.domain.entities.file import File
    from src.domain.entities.file_version import FileVersion

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=False), server_default=text("now()"))

    # reverse relacje
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    owned_files: Mapped[List["File"]] = relationship(back_populates="owner")
    uploaded_versions: Mapped[List["FileVersion"]] = relationship(back_populates="uploader", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
