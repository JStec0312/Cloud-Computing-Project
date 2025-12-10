"""Drop unused tables

Revision ID: 57da9110d3b6
Revises: 99f6bbfac818
Create Date: 2025-12-10 00:54:34.145705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57da9110d3b6'
down_revision: Union[str, Sequence[str], None] = '99f6bbfac818'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS package_items CASCADE")
    op.execute("DROP TABLE IF EXISTS packages CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    pass
