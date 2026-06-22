
from datetime import datetime

from sqlalchemy.orm import (Mapped,
                            mapped_column)
from sqlalchemy import(
    String,
    Boolean,
    DateTime,
    func,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.utils.db import Base
from src.user.enums import UserRole
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.tasks.models import TaskModel

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    name:Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email:Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    tasks: Mapped[list["TaskModel"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
    )

    password_hash:Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role:Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        nullable=False
    )
    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_deleted:Mapped[bool] = mapped_column(
        Boolean,
        default = False,
        nullable=False
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

    deleted_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
    )

