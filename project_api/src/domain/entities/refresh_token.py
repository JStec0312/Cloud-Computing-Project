from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, TIMESTAMP, text, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.base import Base

if TYPE_CHECKING:
    from src.domain.entities.user import User
    from src.domain.entities.session import Session  # jeśli masz encję Session

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    revoked_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    issued_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),  
    )

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )


    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens",
        foreign_keys=[user_id],
    )

    session: Mapped["Session"] = relationship(
        back_populates="refresh_tokens",
        foreign_keys=[session_id],
    )

    revoked_token: Mapped[Optional["RefreshToken"]] = relationship(
        "RefreshToken",
        remote_side="RefreshToken.id",
        foreign_keys=[revoked_id],
        uselist=False,
        post_update=False,
    )

    revoked_children: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="revoked_token",
        primaryjoin="RefreshToken.revoked_id == RefreshToken.id",
        viewonly=True,
    )


    def __repr__(self) -> str:
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})"
