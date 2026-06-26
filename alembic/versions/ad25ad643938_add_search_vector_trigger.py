"""add search vector trigger

Revision ID: ad25ad643938
Revises: 69f40f7fd170
Create Date: 2026-06-26 00:53:26.011901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad25ad643938'
down_revision: Union[str, Sequence[str], None] = '69f40f7fd170'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
CREATE OR REPLACE FUNCTION update_task_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(
            to_tsvector(
                'english',
                coalesce(NEW.title, '')
            ),
            'A'
        )
        ||
        setweight(
            to_tsvector(
                'english',
                coalesce(NEW.description, '')
            ),
            'B'
        );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")
    op.execute("""
CREATE TRIGGER task_search_vector_trigger
BEFORE INSERT OR UPDATE OF title, description
ON user_tasks
FOR EACH ROW
EXECUTE FUNCTION update_task_search_vector();
""")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
DROP TRIGGER IF EXISTS task_search_vector_trigger
ON user_tasks;
""")

    op.execute("""
DROP FUNCTION IF EXISTS update_task_search_vector();
""")

