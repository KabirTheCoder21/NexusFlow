from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.password_reset.models import PasswordResetTokenModel

class PasswordResetRepository:

    @staticmethod
    async def create(
        db:AsyncSession,
        user_id:UUID,
        token_hash:str,
        expires_at:datetime,
    ):
        token = PasswordResetTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token)

        await db.flush()

        return token
    
    @staticmethod
    async def get_by_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> PasswordResetTokenModel | None:

        result = await db.execute(
            select(PasswordResetTokenModel).where(
                PasswordResetTokenModel.token_hash == token_hash
            )
        )

        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_token(
        db:AsyncSession,
        user_id:UUID,
    ):
        result = await db.execute(
            select(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.user_id==user_id,
                PasswordResetTokenModel.is_used.is_(False)
            )
        )
        return list(result.scalars().all())
    
    
    
    @staticmethod
    async def mark_all_used(
        db:AsyncSession,
        user_id:UUID
    ):
        await db.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.user_id==user_id,
                PasswordResetTokenModel.is_used.is_(False)
            )
            .values(is_used = True)
        )
        await db.flush()
        
    
    @staticmethod
    async def mark_used(
        db: AsyncSession,
        token: PasswordResetTokenModel,
    ) -> None:

        token.is_used = True

        await db.flush()

    @staticmethod
    async def delete(
        db: AsyncSession,
        token: PasswordResetTokenModel,
    ) -> None:

        await db.delete(token)

        await db.flush()