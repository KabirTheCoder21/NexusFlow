from uuid import UUID
import logging

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from src.auth.dtos import RefreshTokenDTO, TokenResponseDTO
from src.user.models import UserModel
from src.user.dtos import ChangePasswordDTO, CreateUserDTO, UserResponseDTO
from src.auth.security import hash_password, verify_password
from src.auth.jwt_config import create_access_token, create_refresh_token, decode_token
from src.user.dtos import LoginDTO, UpdateUserDTO

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


class UserController:

    @staticmethod
    async def register_user(
        db: AsyncSession,
        payload: CreateUserDTO,
    ):
        try:
            exising_user = await db.scalar(
                select(UserModel).where(UserModel.email == payload.email)
            )

            if exising_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered.",
                )
            user = UserModel(
                name=payload.name.strip(),
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("User registered successfully. user_id=%s", user.id)
            return user
        except HTTPException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception("Database error while registering user.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to register user.",
            )
        except Exception:
            await db.rollback()
            logger.exception("Unexcepted error while registering user.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong.",
            )

    @staticmethod
    async def login_user(db: AsyncSession, payload: LoginDTO):
        try:
            user = await db.scalar(
                select(UserModel).where(UserModel.email == payload.email.lower())
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Credentials",
                )
            if user.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Account deleted"
                )
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled"
                )
            is_valid = verify_password(payload.password, user.password_hash)

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Credentials",
                )

            access_token = create_access_token(str(user.id))
            refresh_token = create_refresh_token(str(user.id))
            logger.info("user logged in successfully. user id = %s", user.id)

            return TokenResponseDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except HTTPException:
            raise
        except SQLAlchemyError:
            logger.exception("Database error while login")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to Login",
            )
        except Exception:
            logger.exception("Unexcepted error while login")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )

    @staticmethod
    async def refresh_access_token(payload: RefreshTokenDTO, db: AsyncSession):
        try:
            token_payload = decode_token(payload.refresh_token)
            if token_payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token.",
                )
            user_id = token_payload.get("sub")
            user = await db.get(UserModel, UUID(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            new_access_token = create_access_token(str(user.id))
            return TokenResponseDTO(access_token=new_access_token)
        except JWTError:

            raise HTTPException(status_code=401, detail="Invalid refresh token")

    @staticmethod
    async def get_profile(current_user: UserModel):
        try:
            logger.info("Fetching profile | user_id=%s", current_user.id)
            return current_user

        except Exception:
            logger.exception("Error fetching profile")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile",
        )

    @staticmethod
    async def update_profile(
        db: AsyncSession, payload: UpdateUserDTO, current_user: UserModel
    ):
        try:
            logger.info("Updating profile | user_id=%s", current_user.id)
            if payload.name is None and payload.email is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field must be provided",
                )
            if payload.email is not None:
                existing_user = await db.execute(
                    select(UserModel).where(
                        UserModel.email == payload.email,
                        UserModel.id != current_user.id,
                        UserModel.is_deleted == False,
                    )
                )
                existing_user = existing_user.scalar_one_or_none()

                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists",
                    )

            if payload.name is not None:
                current_user.name = payload.name

            if payload.email is not None:
                current_user.email = payload.email

            await db.commit()
            await db.refresh(current_user)
            logger.info("Profile updated successfully | user_id=%s", current_user.id)

            return current_user

        except HTTPException:
            raise

        except SQLAlchemyError:

            await db.rollback()

            logger.exception("Database error while updating profile")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update profile",
            )

        except Exception:

            await db.rollback()

            logger.exception("Unexpected error while updating profile")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )

    @staticmethod
    async def change_password(
        db: AsyncSession, current_user: UserModel, payload: ChangePasswordDTO
    ):
        try:
            logger.info("Password change requested | user_id=%s", current_user.id)
            if not verify_password(payload.old_password, current_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Old password is incorrect",
                )

            if payload.old_password == payload.new_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from old password",
                )

            current_user.password_hash = hash_password(payload.new_password)

            await db.commit()

            logger.info("Password changed successfully | user_id=%s", current_user.id)

            await db.refresh(current_user)

            return {"message": "Password changed successfully"}
        except HTTPException:
            raise
        except SQLAlchemyError:

            await db.rollback()

            logger.exception("Database error while changing password")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to change password",
            )

        except Exception:

            await db.rollback()

            logger.exception("Unexpected error while changing password")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )
