from datetime import datetime, timedelta, timezone

from jose import jwt
import uuid
from src.utils.settings import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
REFRESH_TOKEN_SECRET = settings.REFRESH_TOKEN_SECRET
ALGORITHM = settings.JWT_ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(user_id: str,session_id: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "session_id": session_id,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        ACCESS_TOKEN_SECRET,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: str,
    session_id: str,):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "session_id": session_id,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        REFRESH_TOKEN_SECRET,
        algorithm=ALGORITHM,
    )


def decode_token(token: str,secret: str,):
    return jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
    )