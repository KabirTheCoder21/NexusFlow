import asyncio
import logging

from src.celery_app import celery_app
from src.email.service import EmailService

logger = logging.getLogger(__name__)

@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(
    email: str,
    reset_link: str,
    raw_token: str,
):
    """
    Celery task to send password reset email in background.
    """
    try:
        asyncio.run(
            EmailService.send_password_reset_email(
                email=email,
                reset_link=reset_link,
                raw_token=raw_token,
            )
        )

        logger.info(
            "Password reset email queued successfully for %s",
            email,
        )

    except Exception:
        logger.exception(
            "Failed to send password reset email to %s",
            email,
        )
        raise