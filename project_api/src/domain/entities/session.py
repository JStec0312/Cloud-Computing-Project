from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.user import User
    

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=False), server_default=text("now()"))
    ended_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=False))
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    ip_inet: Mapped[Optional[str]] = mapped_column(INET)
    user: Mapped[Optional["User"]] = relationship(back_populates="sessions")

    #reverse relacje
    refresh_tokens = relationship("RefreshToken", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Session(id={self.id}, user_id={self.user_id}, started_at={self.started_at}, ended_at={self.ended_at})"