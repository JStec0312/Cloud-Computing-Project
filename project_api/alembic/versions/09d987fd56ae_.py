"""empty message

Revision ID: 09d987fd56ae
Revises: d42e42fe9d78
Create Date: 2025-10-30 11:19:46.961226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09d987fd56ae'
down_revision: Union[str, Sequence[str], None] = 'd42e42fe9d78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE op_type ADD VALUE IF NOT EXISTS 'refresh_token';")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER type op_type DROP VALUE 'refresh_token';")



