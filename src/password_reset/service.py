from datetime import datetime, timedelta, timezone
import logging

from fastapi import HTTPException,status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import (
    generate_password_reset_token,
    hash_password,
    hash_password_reset_token,
)

from src.auth.session_repository import SessionRepository
from src.password_reset.repository import PasswordResetRepository
from src.user.controller import UserController

logger = logging.getLogger(__name__)


class PasswordResetService:
    RESET_TOKEN_EXPIRY_MINUTES = 15

    @staticmethod
    async def create_reset_token(db: AsyncSession, email: str):
        user = await UserController.get_user_by_email(db, email=email)
        if not user:
            # return {
            #     "message": "If the account exists, password reset instructions have been sent."
            # }
            logger.info(
                "Password reset requested for unknown email: %s",
                email,
            )

            return None
        await PasswordResetRepository.mark_all_used(
            db,
            user_id=user.id
        )
        raw_token = generate_password_reset_token()
        hashed_token = hash_password_reset_token(
            raw_token
        )
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=15)
        )
        try:
            await PasswordResetRepository.create(
                db=db,
                user_id=user.id,
                token_hash=hashed_token,
                expires_at=expires_at
            )
            await db.commit()
            logger.info(
                "Password reset token created for user=%s",
                user.id,
            )
            return raw_token
        except SQLAlchemyError:

            await db.rollback()

            logger.exception(
                "Failed creating password reset token for user=%s",
                user.id,
            )

            raise

    @staticmethod
    async def reset_password(
            db:AsyncSession,
            token:str,
            new_password:str):
        token_hash = hash_password_reset_token(token)
        reset_token = await PasswordResetRepository.get_by_hash(
            db,token_hash
        )
        if not reset_token:
            logger.warning(
                "Invalid password reset token."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token.",
            )
        
        if reset_token.is_used:
            logger.warning(
                "Password reset token already used."
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token already used.",
            )
        
        if reset_token.expires_at <= datetime.now(timezone.utc):
            await PasswordResetRepository.mark_used(
                db,
                reset_token,
            )
            await db.commit()
            logger.warning(
                "Password reset token expired."
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token expired.",
            )
        user = await UserController.get_by_id(
            db,
            reset_token.user_id
        )

        if not user:
            logger.error(
                "User not found for reset token."
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        password_hash = hash_password(new_password)

        try:
            await UserController.update_password(
                db,user,password_hash
            )
            await PasswordResetRepository.mark_used(
                db,reset_token
            )
            await SessionRepository.revoke_all_sessions(
                db,
                user.id,
            )
            await db.commit()
            logger.info(
                "Password reset successful for user=%s",
                user.id,
            )
        except SQLAlchemyError:

            await db.rollback()

            logger.exception(
                "Failed resetting password."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to reset password.",
            )


        



              

        
