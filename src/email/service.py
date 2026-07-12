from fastapi_mail import FastMail
from fastapi_mail import MessageSchema
from fastapi_mail import MessageType

from jinja2 import Environment
from jinja2 import FileSystemLoader
from src.email.config import config
import logging

logger = logging.getLogger(__name__)

env = Environment(
    loader=FileSystemLoader("templates")
)

class EmailService:
    @staticmethod
    async def send_password_reset_email(
        email: str,
        reset_link: str,
        raw_token:str
    ):
        message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        template_body={
            "token":raw_token,
            "reset_link": reset_link
        },
        subtype=MessageType.html)

        fm = FastMail(config)
        try:

            await fm.send_message(
                message,
                template_name="password_reset_templates.html",
            )

            logger.info(
                "Password reset email sent to %s",
                email,
            )

        except Exception:

            logger.exception(
                "Failed sending password reset email to %s",
                email,
            )
            raise