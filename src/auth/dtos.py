from dataclasses import dataclass

from pydantic import BaseModel

from src.auth.models import UserSessionModel
from src.user.models import UserModel

class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshTokenDTO(BaseModel):
    refresh_token: str

class CurrentUser:
    user: UserModel
    session: UserSessionModel
