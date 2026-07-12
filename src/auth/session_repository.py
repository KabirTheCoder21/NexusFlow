from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


from datetime import datetime, timezone
from src.auth.security import hash_refresh_token
from src.user.models import UserSessionModel


class SessionRepository:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
        refresh_token: str,
        expires_at: datetime,
    ) -> UserSessionModel:
        """
        Create a new user session.
        """

        session = UserSessionModel(
            id=session_id,
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )

        db.add(session)

        await db.flush()

        return session

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: UUID,
    ) -> UserSessionModel | None:
        """
        Fetch session using session id.
        """

        result = await db.execute(
            select(UserSessionModel).where(
                UserSessionModel.id == session_id,
                UserSessionModel.is_revoked==False
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def update_refresh_token(
        db: AsyncSession,
        session: UserSessionModel,
        refresh_token: str,
        expires_at: datetime,
    ) -> UserSessionModel:
        """
        Update refresh token after rotation.
        """

        session.refresh_token_hash = hash_refresh_token(refresh_token)
        session.expires_at = expires_at
        session.last_used_at = datetime.now(timezone.utc)

        await db.flush()

        return session

    @staticmethod
    async def revoke_all_sessions(db:AsyncSession,
                                  user_id:UUID):
        await db.execute(
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id==user_id,
                UserSessionModel.is_revoked.is_(False)
            )
            .values(
                is_revoked = True
            )
        )
        await db.flush()

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        session: UserSessionModel,
    ) -> None:
        """
        Revoke a session.
        """

        session.is_revoked = True

        await db.flush()

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session: UserSessionModel,
    ) -> None:
        """
        Permanently delete a session.
        """

        await db.delete(session)

        await db.flush()
    
    @staticmethod
    async def enforce_session_limit(
        db:AsyncSession,
        user_id:UUID,
        max_sessions:int=2
    ):
        """
        Ensures a user has at most `max_sessions` active sessions.
        Deletes the oldest active session(s) if necessary.
        """
        active_sessions =  await db.scalar(
            select(func.count())
            .select_from(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.is_revoked==False
            )
        )

        if active_sessions<max_sessions:
            return 
        
        session_to_remove = active_sessions-max_sessions+1
        oldest_sessions = (await db.scalars(
            select(UserSessionModel)
            .where(
                UserSessionModel.user_id==user_id,
                UserSessionModel.is_revoked.is_(False)
            )
            .order_by(UserSessionModel.last_used_at.asc())
            .limit(session_to_remove)
        )
).all()
        for session in oldest_sessions:
            await db.delete(session)

        