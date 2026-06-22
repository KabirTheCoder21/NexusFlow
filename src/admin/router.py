from typing import Sequence
from uuid import UUID
from fastapi import APIRouter,Depends,status
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.admin.dtos import DashboardResponseDTO
from src.admin.controller import AdminController
from src.user.models import UserModel
from src.auth.dependencies import get_current_admin
from src.utils.db import get_db
from src.user.dtos import UserResponseDTO
from src.user.router import MessageResponseDTO
from src.user.enums import UserRole

admin_routes = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@admin_routes.get(
    "/users",
    response_model=Sequence[UserResponseDTO],
    status_code=status.HTTP_200_OK
)
async def get_all_users(
    current_admin:UserModel = Depends(
        get_current_admin
    ),
    db:AsyncSession = Depends(get_db)
):
    return await AdminController.get_all_user(
        db=db
    )

@admin_routes.get(
    "/dashboard",
    response_model = DashboardResponseDTO,
    status_code = status.HTTP_200_OK
)
async def get_dashboard_stats(
    db:AsyncSession=Depends(get_db),
    current_user:UserModel = Depends(get_current_admin)
):
    return await AdminController.get_dashboard_stats(db=db)

@admin_routes.delete(
    "/delete",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id:UUID,
    db:AsyncSession=Depends(get_db),
    current_user:UserModel = Depends(get_current_admin)
):
    return await AdminController.delete_user(db=db,
                                             user_id=user_id,
                                             current_user=current_user)

@admin_routes.patch(
    "/restore",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK)
async def restore_user(
    user_id:UUID,
    db:AsyncSession=Depends(get_db),
    current_user:UserModel = Depends(get_current_admin)):
    return await AdminController.restore_user(
        db = db,
        user_id = user_id
    )

@admin_routes.patch(
    "/update-staus",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_200_OK)
async def update_user_status(user_id:UUID,is_active:bool=Query(...,description="Set user status: true = active, false = inactive"),db:AsyncSession=Depends(get_db),current_user:UserModel=Depends(get_current_admin)):
    return await AdminController.update_user_status(user_id=user_id,
                                                    is_active=is_active,
                                                    db=db,
                                                    current_user=current_user)

@admin_routes.patch(
    "/update-role",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id:UUID,
    role:UserRole=Query(...),
    db:AsyncSession = Depends(get_db),
    current_user:UserModel = Depends(get_current_admin)):
    return await AdminController.update_user_role(
        user_id=user_id,
        role = role,
        db=db,
        current_user=current_user
    )