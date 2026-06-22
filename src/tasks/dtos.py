
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict,Field
from typing import Generic, TypeVar, List

T = TypeVar("T")


class CreateTaskDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title : str = Field(...,min_length=1,max_length=255)
    description : str|None = None

class TaskResponseDTO(BaseModel):
    id:UUID
    title:str
    description:str|None = None
    is_completed:bool
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
    is_completed : bool | None = None
