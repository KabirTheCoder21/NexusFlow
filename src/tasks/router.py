
from typing import Sequence
from fastapi import APIRouter,Depends,status
from sqlalchemy.ext.asyncio import AsyncSession
from src.tasks.controller import TaskController
from src.tasks.dtos import (
    CreateTaskDTO,
    PaginatedResponse,
    TaskResponseDTO,
    UpdateTaskDTO,
    UpdateTaskStatusDTO
)
from src.auth.dependencies import (get_current_user)
from uuid import UUID
from src.utils.db import get_db
from src.tasks.models import TaskModel
from src.user.models import UserModel
from src.user.dtos import MessageResponseDTO
from src.tasks.enums import TaskStatus
from src.tasks.dtos import MessageResponseDTO


task_routes = APIRouter(prefix="/tasks",
                        tags=["Tasks"]
                        )

@task_routes.post(
    "/create",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    payload: CreateTaskDTO,
    db: AsyncSession = Depends(get_db),
    current_user:UserModel = Depends(
        get_current_user
    )
) -> TaskModel:
    return await TaskController.create_task(
        db=db,
        payload=payload,
        current_user=current_user
    )

@task_routes.get(
    "/getAllTask",
    response_model=PaginatedResponse[TaskResponseDTO],
    status_code=status.HTTP_200_OK
)
async def get_tasks(
    page:int = 1,
    limit: int = 10,
    current_user:UserModel = Depends(
        get_current_user
    ),
    db:AsyncSession = Depends(get_db)
):
    data, total, page, limit, total_pages = await TaskController.get_task(db=db,
        current_user=current_user,
        page=page,
        limit=limit)

    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@task_routes.get(
    "/getTaskByID",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_200_OK
)
async def get_task_by_id(
        task_id:UUID,
        db:AsyncSession = Depends(get_db),
        current_user:UserModel = Depends(get_current_user)):
    return await TaskController.get_task_by_id(db=db,task_id=task_id,current_user=current_user)


@task_routes.patch(
    "/updateTask",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_200_OK
)
async def update_task(
    task_id:UUID,
    payload:UpdateTaskDTO,
    current_user:UserModel = Depends(
        get_current_user
    ),
    db:AsyncSession = Depends(get_db)
):
    return await TaskController.update_task(
        id=task_id,
        payload=payload,
        db=db,
        current_user=current_user
    )

@task_routes.delete(
    "/deleteTask",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_task(
    task_id:UUID,
    current_user:UserModel = Depends(
        get_current_user
    ),
    db:AsyncSession = Depends(get_db)
):
    return await TaskController.delete_task(
        task_id=task_id,
        db = db,
        current_user=current_user
    )

@task_routes.patch(
    "/recoverTask",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDTO
)
async def recover_task(
    task_id:UUID,
    current_user:UserModel = Depends(
        get_current_user
    ),
    db:AsyncSession = Depends(get_db)
):
    return await TaskController.restore_task(
        task_id=task_id,
        db=db,
        current_user=current_user
    )

@task_routes.patch(
    "/update_task_status",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_200_OK
)
async def update_task_status(
    task_id:UUID,
    payload:TaskStatus,
    db:AsyncSession = Depends(get_db),
    current_user:UserModel = Depends(get_current_user)
) -> MessageResponseDTO:
    return await TaskController.update_status(task_id=task_id,
                                              task_status=payload,
                                              db=db,
                                              current_user=current_user)