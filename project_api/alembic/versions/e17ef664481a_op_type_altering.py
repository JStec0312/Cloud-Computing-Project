"""op_type altering

Revision ID: e17ef664481a
Revises: 881a8798e092
Create Date: 2025-11-26 17:02:23.931558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e17ef664481a'
down_revision: Union[str, Sequence[str], None] = '881a8798e092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE op_type ADD VALUE IF NOT EXISTS 'file_upload_attempt';")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER type op_type DROP VALUE 'file_upload_attempt';")
