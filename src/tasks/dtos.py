
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict,Field
from typing import Generic, TypeVar, List

from src.tasks.enums import TaskStatus

T = TypeVar("T")


class CreateTaskDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title : str = Field(...,min_length=1,max_length=255)
    description : str|None = None

class TaskResponseDTO(BaseModel):
    id:UUID
    title:str
    description:str|None = None
    status : TaskStatus
    created_at : datetime
    updated_at : datetime
    model_config = {
        "from_attributes":True
    }

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    limit: int
    page: int
    total_pages: int
    data: List[T]

class UpdateTaskDTO(BaseModel):
    title : str | None = Field(default=None,min_length=1,max_length=255)
    description : str | None = None

class UpdateTaskStatusDTO(BaseModel):
    status: TaskStatus

class MessageResponseDTO(BaseModel):
    msg:str