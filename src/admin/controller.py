 
from typing import Sequence
from fastapi import HTTPException,status
from sqlalchemy import select,func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.admin.dtos import DashboardResponseDTO
from src.user.models import UserModel, UserRole
from src.tasks.models import TaskModel
import logging
from datetime import datetime, UTC
from uuid import UUID

from src.user.dtos import MessageResponseDTO
from src.tasks.enums import TaskStatus



logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

class AdminController:
    
    @staticmethod
    async def get_all_user(
        db:AsyncSession
    ) -> Sequence[UserModel]:
        try:
            result = await db.execute(select(UserModel)
                                      .where(
                                          UserModel.is_deleted==False)
                                        .order_by(UserModel.created_at.desc()))
            users = result.scalars().all()
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Users not Found."
                )
            return users
        except HTTPException:
            raise
        except SQLAlchemyError:
            logger.exception(
            "Database error while fetching users."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = "Unable to fetch users."
            )
        except Exception:
            logger.exception(
                "Unexcepted error while login"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = "Something went wrong"
            )

    @staticmethod
    async def get_dashboard_stats(
        db:AsyncSession
    ):
        try:
            logger.info(
            "Fetching dashboard statistics")

            total_users = (await db.execute(
                select(func.count(UserModel.id))
            )).scalar() or 0

            active_user = (await db.execute(
                select(func.count(UserModel.id))
                .where(UserModel.is_active==True,
                       UserModel.is_deleted==False)
            )).scalar() or 0

            inactive_user = total_users-active_user

            deleted_user = (await db.execute(
                select(func.count(UserModel.id))
                .where(UserModel.is_deleted==True)
            )).scalar() or 0

            total_tasks = (await db.execute(
                select(func.count(TaskModel.id))
                .where(TaskModel.is_deleted==False)
            )).scalar() or 0

            completed_tasks = (await db.execute(
                select(func.count(TaskModel.id))
                .where(TaskModel.status==TaskStatus.COMPLETED,
                       TaskModel.is_deleted==False)
            )).scalar() or 0
            pending_tasks = total_tasks - completed_tasks

            return DashboardResponseDTO(
                total_users=total_users,
                active_users=active_user,
                inactive_user=inactive_user,
                deleted_users=deleted_user,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                pending_tasks=pending_tasks)
        
        except HTTPException:
            raise

        except SQLAlchemyError:
            logger.exception(
            "Database error while fetching dashboard")

            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch dashboard statistics")
        
        except Exception:
            logger.exception(
                "Unexpected error while fetching dashboard")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong"
            )

    @staticmethod
    async def delete_user(
        db:AsyncSession,
        user_id:UUID,
        current_user:UserModel
    ):
        try:
                if user_id == current_user.id:
                    raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot delete your own account.")
                
                logger.info("Attempting to delete user.")
                result = await db.execute(
                  select(UserModel)
                  .where(
                      UserModel.id == user_id,
                      UserModel.is_deleted == False))
                user = result.scalar_one_or_none()
                if not user:
                   raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found")
                user.is_deleted=True
                user.is_active=False
                user.deleted_at = datetime.now(UTC)
                await db.commit()
                logger.info(f"User soft deleted successfully | user_id={user_id}")
                return None
        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(
            "Database error while deleting user.")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete user.")
        except Exception:
            await db.rollback()
            logger.exception("Unexcpected error while deleting user.")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.")
        
    @staticmethod
    async def restore_user(
        db:AsyncSession,
        user_id:UUID):
        try:

            logger.info(f"Restoring user | user_id={user_id}")

            result = await db.execute(select(UserModel)
                                      .where(UserModel.id == user_id,
                                          UserModel.is_deleted==True))
            
            user = result.scalar_one_or_none()

            if not user:

                logger.warning(
                f"Restore failed | user not found | user_id={user_id}"
                )

                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted user not found"
                )
            user.is_deleted = False
            user.deleted_at = None

            await db.commit()
            await db.refresh(user)

            logger.info(
            f"User restored successfully | user_id={user_id}"
            )
            return user
        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f" Database error restoring task | user_id={user_id}")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore task")
        except Exception:
            await db.rollback()
            logger.exception(f" Unexpected error while restoring task | user_id={user_id}")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.")

    @staticmethod
    async def update_user_status(
        db:AsyncSession,
        user_id:UUID,
        is_active:bool,
        current_user:UserModel):
        try:
            if user_id == current_user.id:
                raise HTTPException(
                status_code=400,
                detail="You cannot change your own status.")
            
            logger.info(
            "Attempting to update user status. user_id=%s, is_active=%s",
            user_id,
            is_active)

            result = await db.execute(
            select(UserModel).where(
            UserModel.id == user_id,
            UserModel.is_deleted.is_(False)))

            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404,
                detail="User Not Found.")
            
            if user.is_active==is_active:
                raise HTTPException(status_code=409,
                detail=(
                "User is already active."
                if is_active
                else "User is already inactive."))
            
            user.is_active = is_active
            await db.commit()

            logger.info("Updated user status. user_id = %s",user_id)

            # await db.refresh(user) --as we are not sending user model then doesn't nees to run refresh.

            return MessageResponseDTO(
                message="Status updated successfully."
            )
        
        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(" Database error while updating user status. | user_id=%s",user_id)
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status.")
        except Exception:
            await db.rollback()
            logger.exception(" Unexpected error while updating user status. | user_id=%s",user_id)
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.")

    @staticmethod
    async def update_user_role(user_id:UUID,role:UserRole,db:AsyncSession,current_user:UserModel):
        try:
            if user_id == current_user.id:
                raise HTTPException(
                status_code=400,
                detail="You cannot change your own role.")
            logger.info(
            "Attempting to update user role. user_id=%s",user_id)
            result = await db.execute(
                select(UserModel)
                .where(UserModel.id==user_id,
                    UserModel.is_deleted.is_(False)))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404,
                detail="User Not found.")
            
            if user.role==role:
                raise HTTPException(status_code=409,
                detail=(f"User is already {role.value}."))
            old_role = user.role
            user.role = role
            await db.commit()

            logger.info("User role updated successfully. target_user=%s, updated_by=%s, old_role=%s, new_role=%s",
            user_id,
            current_user.id,
            old_role,
            role)

            return MessageResponseDTO(message=f"User role updated from {old_role.value} to {role.value}")
        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(" Database error while updating user role. | user_id=%s",user_id)
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role.")
        except Exception:
            await db.rollback()
            logger.exception(" Unexpected error while updating user role. | user_id=%s",user_id)
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.")

            
        