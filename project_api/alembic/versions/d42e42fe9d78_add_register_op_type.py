"""add register op type

Revision ID: d42e42fe9d78
Revises: e6e0c97bf434
Create Date: 2025-10-28 17:22:03.125422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd42e42fe9d78'
down_revision: Union[str, Sequence[str], None] = 'e6e0c97bf434'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE op_type ADD VALUE IF NOT EXISTS 'user_register';")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER type op_type DROP VALUE 'user_register';")
