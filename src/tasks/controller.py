from turtle import title, update
from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy import asc, desc, func, literal_column
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, UTC

from sqlalchemy.sql.elements import and_, or_
from src.tasks.models import TaskModel
from src.tasks.dtos import (
    CreateTaskDTO,
    MessageResponseDTO,
    PaginatedTaskResponse,
    PaginationDTO,
    TaskListFilters,
    TaskResponseDTO,
    TaskStatus,
    UpdateTaskDTO,
    UpdateTaskStatusDTO,
)
from src.user.models import UserModel
from src.tasks.constant import ALLOWED_TASK_STATUS_TRANSITIONS
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


class TaskController:

    @staticmethod
    async def create_task(
        db: AsyncSession, payload: CreateTaskDTO, current_user: UserModel
    ) -> TaskModel:

        try:
            task = TaskModel(
                title=payload.title.strip(),
                description=payload.description,
                user_id=current_user.id,
            )

            db.add(task)

            await db.commit()

            await db.refresh(task)

            logger.info("Task created successfully. task_id=%s", task.id)

            return task

        except SQLAlchemyError as e:

            await db.rollback()

            logger.exception("Database error while creating task")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create task",
            )

        except Exception:

            await db.rollback()

            logger.exception("Unexpected error while creating task")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )

    @staticmethod
    async def get_task(
        db: AsyncSession, current_user: UserModel, filters: TaskListFilters
    ):
        try:
            logger.info(
                f"Fetching tasks | "
                f"user_id={current_user.id} | "
                f"page={filters.page} | "
                f"limit={filters.limit} | "
                f"search={filters.search} | "
                f"status={filters.status}"
            )
            conditions = [
                TaskModel.is_deleted.is_(False),
                TaskModel.user_id == current_user.id,
            ]

            search_vector = None
            blended_score = None

            if filters.search:
                # conditions.append(TaskModel.title.ilike(f"%{filters.search}%"))
                search_query = filters.search.strip()
                ts_query = func.websearch_to_tsquery("english", search_query)
                search_vector = func.setweight(
                    func.to_tsvector("english", func.coalesce(TaskModel.title, "")),
                    literal_column("'A'"),
                ).op("||")(
                    func.setweight(
                        func.to_tsvector(
                            "english", func.coalesce(TaskModel.description, "")
                        ),
                        literal_column("'B'"),
                    )
                )
                title_sim = func.similarity(TaskModel.title, search_query)

                desc_sim = func.similarity(
                    func.coalesce(TaskModel.description, ""), search_query
                )

                fts_rank = func.ts_rank_cd(search_vector, ts_query)
                blended_score = (fts_rank * 2.0) + (title_sim * 1.5) + (desc_sim * 0.5)
                conditions.append(
                    or_(
                        search_vector.op("@@")(ts_query),
                        func.word_similarity(search_query, TaskModel.title) > 0.35,
                        func.word_similarity(
                            search_query, func.coalesce(TaskModel.description, "")
                        )
                        > 0.40,
                    )
                )

                title_sim = func.similarity(TaskModel.title, search_query)

                desc_sim = func.similarity(
                    func.coalesce(TaskModel.description, ""), search_query
                )
                fts_rank = func.ts_rank_cd(search_vector, ts_query)

            if filters.status:
                conditions.append(TaskModel.status == filters.status)

            count_stmt = select(func.count(TaskModel.id)).where(and_(*conditions))

            total = (await db.execute(count_stmt)).scalar_one()
            if total == 0:
                return {
                    "items": [],
                    "pagination": {
                        "page": filters.page,
                        "limit": filters.limit,
                        "total": 0,
                        "total_pages": 0,
                    },
                }
            total_pages = (total + filters.limit - 1) // filters.limit

            page = min(filters.page, total_pages)
            offset = (page - 1) * filters.limit

            # sort_column = getattr(TaskModel, filters.sort_by, TaskModel.updated_at)
            SORT_MAPPING = {
                "created_at": TaskModel.created_at,
                "updated_at": TaskModel.updated_at,
                "title": TaskModel.title,
            }

            sort_column = SORT_MAPPING.get(filters.sort_by, TaskModel.updated_at)

            if filters.search and blended_score is not None:

                order_clause = [blended_score.desc(), TaskModel.created_at.desc()]

            else:

                order_clause = [
                    (
                        asc(sort_column)
                        if filters.sort_order == "asc"
                        else desc(sort_column)
                    )
                ]

            stmt = (
                select(TaskModel)
                .where(and_(*conditions))
                .order_by(*order_clause)
                .offset(offset)
                .limit(filters.limit)
            )

            result = await db.execute(stmt)
            tasks = result.scalars().all()
            logger.info(
                f"Tasks fetched successfully | "
                f"user_id={current_user.id} | "
                f"returned={len(tasks)} | "
                f"total={total}"
            )

            return PaginatedTaskResponse(
                items=[TaskResponseDTO.model_validate(task) for task in tasks],
                pagination=PaginationDTO(
                    page=page, limit=filters.limit, total=total, total_pages=total_pages
                ),
            )
        except Exception:
            logger.exception(f"Failed fetching tasks | " f"user_id={current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch tasks",
            )

    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: UUID, current_user: UserModel):
        try:
            logger.info("Attempting to fetch task by id.")
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == task_id,
                    TaskModel.user_id == current_user.id,
                    TaskModel.is_deleted == False,
                )
            )
            task = result.scalar_one_or_none()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found for the provided task id.",
                )
            return task
        except HTTPException:
            raise
        except SQLAlchemyError:
            logger.exception("Database error while fetching task.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to fetch task.",
            )
        except Exception:
            logger.exception("Something went wrong")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )

    #     @staticmethod
    #     async def search_task(
    #     query: str,
    #     db: AsyncSession,
    #     current_user: UserModel,
    #     limit: int = 20
    # ):
    #         query = query.strip()
    #         if not query:
    #             return []

    #     # 1. Generate similarities and ts_query
    #         ts_query = func.websearch_to_tsquery("english", query)
    #         title_sim = func.similarity(TaskModel.title, query)
    #         desc_sim = func.similarity(func.coalesce(TaskModel.description, ""), query)

    #     # 2. Re-use the vector generation (Note: See DB optimization below)
    #         search_vector = (
    #         func.setweight(func.to_tsvector("english", func.coalesce(TaskModel.title, "")), literal_column("'A'"))
    #         .op("||")(
    #             func.setweight(func.to_tsvector("english", func.coalesce(TaskModel.description, "")), literal_column("'B'"))
    #         )
    #     )

    #     # 3. Calculate FTS Rank
    #         fts_rank = func.ts_rank_cd(search_vector, ts_query)

    #     # 4. Create a Blended "Google-Like" Score
    #     # Combines Exact matches (FTS) + Typo/Partial matches (Trigram)
    #     # Titles are given a heavy multiplier to ensure title matches float to the top
    #         blended_score = (fts_rank * 2.0) + (title_sim * 1.5) + (desc_sim * 0.5)

    #         stmt = (
    #         select(TaskModel)
    #         .where(
    #             TaskModel.user_id == current_user.id,
    #             TaskModel.is_deleted == False,
    #             or_(

    #                 search_vector.op("@@")(ts_query),

    #                 # FIX 1: Use word_similarity
    #                 # FIX 2: query MUST be the first argument
    #                 func.word_similarity(
    #                     query,
    #                     TaskModel.title
    #                 ) > 0.35,

    #                 func.word_similarity(
    #                     query,
    #                     func.coalesce(TaskModel.description, "")
    #                 ) > 0.40,
    #             )
    #         )
    #         .order_by(
    #             blended_score.desc(),
    #             TaskModel.created_at.desc()
    #         )
    #         .limit(limit)
    #     )

    #         result = await db.execute(stmt)
    #         return result.scalars().all()

    @staticmethod
    async def update_task(
        db: AsyncSession, current_user: UserModel, id: UUID, payload: UpdateTaskDTO
    ):
        try:
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == id, TaskModel.user_id == current_user.id
                )
            )
            task = result.scalar_one_or_none()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
                )
            update_data = payload.model_dump(exclude_unset=True)
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided for update",
                )

            for key, value in update_data.items():
                setattr(task, key, value)

            await db.commit()
            await db.refresh(task)

            return task

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while updating task")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task",
            )

    @staticmethod
    async def delete_task(task_id: UUID, current_user: UserModel, db: AsyncSession):
        try:
            logger.info(f"Deleting task | task_id={task_id}")
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == task_id,
                    TaskModel.user_id == current_user.id,
                    TaskModel.is_deleted == False,
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
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
                detail="Failed to delete task",
            )

    @staticmethod
    async def restore_task(task_id: UUID, current_user: UserModel, db: AsyncSession):
        try:
            logger.info(f"Restoring task | task_id={task_id}")
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == task_id,
                    TaskModel.user_id == current_user.id,
                    TaskModel.is_deleted == True,
                )
            )
            task = result.scalar_one_or_none()
            if not task:
                logger.warning(f"Restore failed | task not found | task_id={task_id}")

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
                )
            task.is_deleted = False
            task.deleted_at = None

            await db.commit()
            await db.refresh(task)
            logger.info(f"Task restored successfully | task_id={task_id}")

            return task
        except HTTPException:
            raise
        except Exception:
            logger.exception(f"Error restoring task | task_id={task_id}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore task",
            )

    @staticmethod
    async def update_status(
        task_id: UUID,
        task_status: TaskStatus,
        current_user: UserModel,
        db: AsyncSession,
    ):
        try:
            logger.info(f"Attempting to update task| task_id={task_id}")
            result = await db.execute(
                select(TaskModel).where(
                    TaskModel.id == task_id,
                    TaskModel.user_id == current_user.id,
                    TaskModel.is_deleted == False,
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            if task_status == task.status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Task already in this status.",
                )

            if task_status not in ALLOWED_TASK_STATUS_TRANSITIONS[task.status]:
                raise HTTPException(status_code=400, detail="Invalid status transition")
            old_status = task.status
            task.status = task_status

            logger.info(f"Task status updated from {old_status} to {task_status}.")
            await db.commit()

            return MessageResponseDTO(msg="Task status updated successfully.")

        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()

            logger.exception("Database error while updating task status.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update task status.",
            )
        except Exception:
            await db.rollback()

            logger.exception(f"Error updating task status. | task_id={task_id}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task status.",
            )
