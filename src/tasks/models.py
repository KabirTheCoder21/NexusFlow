import uuid
from datetime import datetime,timezone

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.user.models import UserModel

class TaskModel(Base):
    __tablename__ = "user_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id",ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user:Mapped["UserModel"] = relationship(
        back_populates="tasks"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False
)