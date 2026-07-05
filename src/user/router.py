from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dtos import CurrentUser, RefreshTokenDTO, TokenResponseDTO
from src.utils.db import get_db

from src.user.controller import UserController
from src.user.dtos import (
    ChangePasswordDTO,
    CreateUserDTO,
    LoginDTO,
    MessageResponseDTO,
    UpdateUserDTO,
    UserResponseDTO,
)
from src.user.models import UserModel
from src.tasks.router import get_current_user

user_routes = APIRouter(prefix="/users", tags=["Users"])


@user_routes.post(
    "/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED
)
async def register_user(payload: CreateUserDTO, db: AsyncSession = Depends(get_db)):
    return await UserController.register_user(db=db, payload=payload)


@user_routes.post(
    "/login",
    response_model=TokenResponseDTO,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def login_user(payload: LoginDTO, db: AsyncSession = Depends(get_db)):
    return await UserController.login_user(db=db, payload=payload)


@user_routes.post(
    "/refresh",
    response_model=TokenResponseDTO,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
async def refresh_token(payload: RefreshTokenDTO, db: AsyncSession = Depends(get_db)):
    return await UserController.refresh_access_token(payload=payload, db=db)


@user_routes.get(
    "/profile", response_model=UserResponseDTO, status_code=status.HTTP_200_OK
)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return await UserController.get_profile(current_user=current_user)


@user_routes.patch(
    "/update", response_model=UserResponseDTO, status_code=status.HTTP_200_OK
)
async def update_profile(
    payload: UpdateUserDTO,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await UserController.update_profile(
        db=db, payload=payload, current_user=current_user
    )


@user_routes.post(
    "/change-password",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    payload: ChangePasswordDTO,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):

    return await UserController.change_password(
        db=db, payload=payload, current_user=current_user
    )


@user_routes.post(
        "/logout",
        response_model=MessageResponseDTO,
        status_code=status.HTTP_200_OK,
)
async def logout(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserController.logout(
        db=db,
        current_user=current,
    )