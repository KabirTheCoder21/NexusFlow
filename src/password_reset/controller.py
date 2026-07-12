import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.email.settings import email_settings
from src.email.service import EmailService
from src.password_reset.service import PasswordResetService

logger = logging.getLogger(__name__)

class PasswordResetController:

    @staticmethod
    async def forgot_password(
        db:AsyncSession,
        email:str
    ):
        try:
            raw_token = await PasswordResetService.create_reset_token(
                db=db,
                email=email
            )
            if raw_token is None:
                logger.info(
                    "Password reset requested for  unkown email=%s",email
                )
                return {
                    "message":(
                        "If an account exists, "
                        "a password reset email has been sent."
                    )
                }
            reset_link = (
                f"{email_settings.FRONTEND_URL}"
                f"users/reset-password"
                f"?token={raw_token}"
            )

            await EmailService.send_password_reset_email(
                email=email,
                reset_link=reset_link,
                raw_token=raw_token
            )
            
            logger.info(
                "Password reset email successfully sent to %s",
                email,
            )
            return {
                "message": (
                    "If an account exists, "
                    "a password reset email has been sent."
                )
            }
        except SQLAlchemyError:

            logger.exception(
                "Database error while creating password reset token."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process password reset request.",
            )
        
        except Exception:

            logger.exception(
                "Unexpected error during forgot password."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong.",
            )
        
    
    @staticmethod
    async def reset_password(
        db:AsyncSession,
        token:str,
        new_password:str
    ):
        try:
            await PasswordResetService.reset_password(
                db,token,new_password
            )
            logger.info(
                "Password reset completed successfully."
            )

            return {
                "message": "Password reset successfully."
            }
        except HTTPException:
            raise
        except SQLAlchemyError:

            logger.exception(
                "Database error while resetting password."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to reset password.",
            )
        except Exception:

            logger.exception(
                "Unexpected error during password reset."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong.",
            )
        



