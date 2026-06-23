"""add_task_status

Revision ID: 05fccbf4afcf
Revises: 59974676977f
Create Date: 2026-06-22 23:55:52.562415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05fccbf4afcf'
down_revision: Union[str, Sequence[str], None] = '59974676977f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    task_status = sa.Enum(
    "TODO",
    "IN_PROGRESS",
    "COMPLETED",
    name="taskstatus"
)

    task_status.create(op.get_bind(),checkfirst=True)

    op.add_column(
        "user_tasks",
            sa.Column(
            "status",
            task_status,
            nullable=True))

    op.execute("""
        UPDATE user_tasks
        SET status = 'COMPLETED'
        WHERE is_completed = true
        """)

    op.execute("""
        UPDATE user_tasks
        SET status = 'TODO'
        WHERE is_completed = false
        """)

    op.alter_column(
        "user_tasks",
        "status",
        nullable=False
    )


def downgrade() -> None:
    op.drop_column(
    "user_tasks",
    "status")

    sa.Enum(
        "TODO",
        "IN_PROGRESS",
        "COMPLETED",
        name="taskstatus"
        ).drop(op.get_bind(),checkfirst=True)