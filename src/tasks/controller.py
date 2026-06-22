from turtle import title, update
from fastapi import HTTPException,status
from sqlalchemy import desc, func
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, UTC
from src.tasks.models import TaskModel
from src.tasks.dtos import CreateTaskDTO, UpdateTaskDTO
from src.user.models import UserModel
import logging

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

class TaskController:

    @staticmethod
    async def create_task(
        db: AsyncSession,
        payload: CreateTaskDTO,
        current_user: UserModel
    ) -> TaskModel:

        try:
            task = TaskModel(
                title=payload.title.strip(),
                description=payload.description,
                user_id = current_user.id
            )

            db.add(task)

            await db.commit()

            await db.refresh(task)

            logger.info(
                "Task created successfully. task_id=%s",
                task.id
            )

            return task

        except SQLAlchemyError as e:

            await db.rollback()

            logger.exception(
                "Database error while creating task"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create task"
            )

        except Exception:

            await db.rollback()

            logger.exception(
                "Unexpected error while creating task"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong"
            )
    
        
    @staticmethod
    async def get_task(db:AsyncSession,current_user: UserModel, page: int = 1, limit: int = 10):
        try:
            logger.info(f"Fetching tasks | page={page}, limit={limit}")

            page = max(page or 1, 1)
            limit = min(max(limit or 10, 1), 100)

            total = (await db.execute(
                select(func.count(TaskModel.id)).where(TaskModel.is_deleted == False,TaskModel.user_id==current_user.id)
            )).scalar() or 0

            if total == 0:
                return [], 0, 1, limit, 0

            total_pages = (total + limit - 1) // limit

            if page > total_pages:
                page = total_pages
                return [], total, page, limit, total_pages

            skip = (page - 1) * limit

            stmt = (
                select(TaskModel)
                .where(TaskModel.is_deleted == False,
                       TaskModel.user_id == current_user.id)
                .order_by(desc(TaskModel.updated_at))
                .limit(limit)
                .offset(skip)
            )

            result = await db.execute(stmt)
            tasks = result.scalars().all()

            return tasks, total, page, limit, total_pages

        except Exception:
            logger.exception("Error fetching tasks")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch tasks"
            )
        
    @staticmethod
    async def update_task(db:AsyncSession,current_user:UserModel,id:UUID,payload : UpdateTaskDTO):
        try:
            result = await db.execute(select(TaskModel).where(TaskModel.id==id,TaskModel.user_id==current_user.id))
            task = result.scalar_one_or_none()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found"
                )
            update_data = payload.model_dump(exclude_unset=True)
            if not update_data:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
                )
            
            for key,value in update_data.items():
                setattr(task,key,value)
            
            await db.commit()
            await db.refresh(task)

            return task

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while updating task")

            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
            )

    @staticmethod
    async def delete_task(
        task_id:UUID,
        current_user:UserModel,
        db:AsyncSession
    ):
        try:
            logger.info(f"Deleting task | task_id={task_id}")
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == task_id,
                    TaskModel.user_id==current_user.id,
                    TaskModel.is_deleted==False
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found"
                )
            task.is_deleted = True
            task.deleted_at = datetime.now(UTC)
            await db.commit()
            logger.info(f"Task soft deleted successfully | task_id={task_id}")
            return None
        except HTTPException:
            raise

        except Exception:
            logger.exception(f"Error deleting task | task_id={task_id}")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
            )
        
    @staticmethod
    async def restore_task(
        task_id:UUID,
        current_user:UserModel,
        db:AsyncSession
    ):
        try:
            logger.info(f"Restoring task | task_id={task_id}")
            result = await db.execute(select(TaskModel).where(
                TaskModel.id==task_id,
                TaskModel.user_id==current_user.id,
                TaskModel.is_deleted==True))
            task = result.scalar_one_or_none()
            if not task:
                logger.warning(
                f"Restore failed | task not found | task_id={task_id}"
                )

                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted task not found"
                )
            task.is_deleted = False
            task.deleted_at = None

            await db.commit()
            await db.refresh(task)
            logger.info(
            f"Task restored successfully | task_id={task_id}"
            )

            return task
        except HTTPException:
            raise
        except Exception:
            logger.exception(
            f"Error restoring task | task_id={task_id}")

            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore task")

