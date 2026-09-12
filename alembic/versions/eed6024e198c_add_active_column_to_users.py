"""add_active_column_to_users

Revision ID: eed6024e198c
Revises: c970f368ed81
Create Date: 2025-04-24 18:06:40.460974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eed6024e198c'
down_revision: Union[str, None] = 'c970f368ed81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')))

def downgrade() -> None:
    op.drop_column('users', 'active')
