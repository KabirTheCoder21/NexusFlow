from datetime import datetime
from uuid import UUID, uuid4
from xmlrpc import server

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.db import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.user.models import UserModel

class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id : Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id:Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id",ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash:Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True
    )
    is_used:Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    expires_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    user:Mapped["UserModel"] = relationship(
        back_populates="password_reset_tokens"
    )
