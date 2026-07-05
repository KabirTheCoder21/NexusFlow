from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import logging

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from src.auth.dependencies import CurrentUser
from src.auth.dtos import RefreshTokenDTO, TokenResponseDTO
from src.auth.session_repository import SessionRepository
from src.user.models import UserModel
from src.user.dtos import ChangePasswordDTO, CreateUserDTO, MessageResponseDTO, UserResponseDTO
from src.auth.security import hash_password, hash_refresh_token, verify_password
from src.auth.jwt_config import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.user.dtos import LoginDTO, UpdateUserDTO
from src.auth.session_repository import SessionRepository
from src.auth.models import UserSessionModel
from src.utils.db import settings

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
    async def login_user(
        db: AsyncSession,
        payload: LoginDTO,
    ):
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
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account deleted",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account disabled",
                )

            if not verify_password(
                payload.password,
                user.password_hash,
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Credentials",
                )

            await SessionRepository.enforce_session_limit(
                db=db,
                user_id=user.id,
            )

            # ---------------------------------------
            # Create Session
            # ---------------------------------------

            session_id = uuid4()

            refresh_token = create_refresh_token(
                user_id=str(user.id),
                session_id=str(session_id),
            )

            await SessionRepository.create_session(
                db=db,
                user_id=user.id,
                session_id=session_id,
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            )

            access_token = create_access_token(
                user_id=str(user.id),
                session_id=str(session_id),
            )

            await db.commit()

            logger.info(
                "User logged in successfully. user_id=%s session_id=%s",
                user.id,
                session_id,
            )

            return TokenResponseDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            )

        except HTTPException:
            await db.rollback()
            raise

        except SQLAlchemyError:
            await db.rollback()

            logger.exception("Database error while login")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to Login",
            )

        except Exception:
            await db.rollback()

            logger.exception("Unexpected error while login")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )

    @staticmethod
    async def refresh_access_token(payload: RefreshTokenDTO, db: AsyncSession):
        try:
            token_payload = decode_token(
                payload.refresh_token, settings.REFRESH_TOKEN_SECRET
            )

            if token_payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type.",
                )

            user_id = token_payload.get("sub")
            session_id = token_payload.get("session_id")

            if not user_id or not session_id:
                raise HTTPException(status_code=401, detailF="Malformed token")

            # 1. Fetch session
            session = await SessionRepository.get_session_by_id(
                db,
                UUID(session_id),
            )

            if not session:
                raise HTTPException(
                    status_code=401, detail="Session invalid or revoked"
                )

            # 2. Verify user matches session
            if str(session.user_id) != user_id:
                raise HTTPException(status_code=401, detail="Session mismatch")

            user = await db.get(UserModel, UUID(user_id))
            if user is None or user.is_deleted or not user.is_active:
                await SessionRepository.revoke_session(db, session)
                await db.commit()

                raise HTTPException(
                    status_code=401,
                    detail="Account unavailable",
                )

            # 3. Verify refresh token hash (anti-replay)
            incoming_hash = hash_refresh_token(payload.refresh_token)

            if incoming_hash != session.refresh_token_hash:
                await SessionRepository.revoke_session(db=db, session=session)
                await db.commit()

                raise HTTPException(
                    status_code=401, detail="Refresh token reuse detected"
                )

            # 3.5. Check session expiration
            if session.expires_at <= datetime.now(timezone.utc):
                await SessionRepository.revoke_session(db, session)
                await db.commit()

                raise HTTPException(status_code=401, detail="Refresh token expired")

            # 4. Rotate refresh token
            new_refresh_token = create_refresh_token(
                user_id=user_id, session_id=session_id
            )

            await SessionRepository.update_refresh_token(
                db=db,
                session=session,
                refresh_token=new_refresh_token,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            )

            # 5. Issue new access token
            new_access_token = create_access_token(user_id, session_id=session_id)

            await db.commit()

            return TokenResponseDTO(
                access_token=new_access_token, refresh_token=new_refresh_token
            )

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    @staticmethod
    async def get_profile(current_user: CurrentUser):
        try:
            logger.info("Fetching profile | user_id=%s", current_user.user.id)
            return current_user.user

        except Exception:
            logger.exception("Error fetching profile")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile",
        )

    @staticmethod
    async def update_profile(
        db: AsyncSession, payload: UpdateUserDTO, current_user: CurrentUser
    ):
        try:
            logger.info("Updating profile | user_id=%s", current_user.user.id)
            if payload.name is None and payload.email is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field must be provided",
                )
            if payload.email is not None:
                existing_user = await db.execute(
                    select(UserModel).where(
                        UserModel.email == payload.email,
                        UserModel.id != current_user.user.id,
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
                current_user.user.name = payload.name

            if payload.email is not None:
                current_user.user.email = payload.email

            await db.commit()
            await db.refresh(current_user.user)
            logger.info(
                "Profile updated successfully | user_id=%s", current_user.user.id
            )

            return current_user.user

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
        db: AsyncSession, current_user: CurrentUser, payload: ChangePasswordDTO
    ):
        try:
            logger.info("Password change requested | user_id=%s", current_user.user.id)
            if not verify_password(
                payload.old_password, current_user.user.password_hash
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Old password is incorrect",
                )

            if payload.old_password == payload.new_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from old password",
                )

            current_user.user.password_hash = hash_password(payload.new_password)

            await db.commit()

            logger.info(
                "Password changed successfully | user_id=%s", current_user.user.id
            )

            await db.refresh(current_user.user)

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
    
    @staticmethod
    async def logout(
        db:AsyncSession,
        current_user:CurrentUser
    ):
        """
        Revoke the current authenticated session.
        Logout is idempotent.
        """
        try:
            if current_user.session.is_revoked:
                logger.warning(
                    "Logout requested for already revoked session | "
                    "user_id=%s session_id=%s",
                    current_user.user.id,
                    current_user.session.id,
                )
                MessageResponseDTO.message = "Already logged out."
                return MessageResponseDTO
            logger.info(
                "Revoking session | user_id=%s session_id=%s",
                current_user.user.id,
                current_user.session.id,
            )
            await SessionRepository.revoke_session(
                db=db,
                session=current_user.session,
            )
            await db.commit()
            logger.info(
                "Session revoked successfully | "
                "user_id=%s session_id=%s",
                current_user.user.id,
                current_user.session.id,
            )

            MessageResponseDTO.message = "Logged out successfully."
            return MessageResponseDTO

        except HTTPException:
            await db.rollback()
            raise

        except SQLAlchemyError:

            await db.rollback()

            logger.exception(
                "Database error while logging out | "
                "user_id=%s session_id=%s",
                current_user.user.id,
                current_user.session.id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to logout.",
            )
        except Exception:

            await db.rollback()

            logger.exception(
                "Unexpected error while logging out | "
                "user_id=%s session_id=%s",
                current_user.user.id,
                current_user.session.id,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong.",
            )
        




        
