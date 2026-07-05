from uuid import UUID

from jose import JWTError

from fastapi import Depends, HTTPException, status

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dtos import CurrentUser
from src.auth.session_repository import SessionRepository
from src.utils.db import get_db

from src.user.models import UserModel

from src.auth.jwt_config import ACCESS_TOKEN_SECRET, decode_token
from src.user.dtos import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    try:
        token = credentials.credentials
        payload = decode_token(token,ACCESS_TOKEN_SECRET)

        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        token_type = payload.get("type")

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        if not user_id or not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Validate session
        session = await SessionRepository.get_session_by_id(
            db,
            UUID(session_id),
        )

        if not session or session.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session invalid or revoked",
            )

        # Validate user
        user = await db.get(UserModel, UUID(user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User deleted",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User disabled",
            )
        
        CurrentUser.user = user
        CurrentUser.session = session
        return CurrentUser

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

async def get_current_admin(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user.user
