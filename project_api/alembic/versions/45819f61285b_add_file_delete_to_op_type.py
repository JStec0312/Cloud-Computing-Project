"""add file delete to op  type

Revision ID: 45819f61285b
Revises: 4771f67cc167
Create Date: 2025-11-28 12:44:41.787767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45819f61285b'
down_revision: Union[str, Sequence[str], None] = '4771f67cc167'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE op_type ADD VALUE IF NOT EXISTS 'file_delete';")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER type op_type DROP VALUE 'file_delete';")
