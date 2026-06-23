from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, Literal, TypeVar, List

from src.tasks.enums import TaskStatus

T = TypeVar("T")


class CreateTaskDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class TaskResponseDTO(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TaskListFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)

    search: str | None = None
    status: TaskStatus | None = None

    sort_by: Literal["created_at", "updated_at", "title", "status"] = "updated_at"

    sort_order: Literal["asc", "desc"] = "desc"


class PaginationDTO(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedTaskResponse(BaseModel):
    items: list[TaskResponseDTO]
    pagination: PaginationDTO


class UpdateTaskDTO(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class UpdateTaskStatusDTO(BaseModel):
    status: TaskStatus


class MessageResponseDTO(BaseModel):
    msg: str
