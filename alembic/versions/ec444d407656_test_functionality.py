"""test_functionality

Revision ID: ec444d407656
Revises: 8747c6dde27f
Create Date: 2025-05-24 14:03:29.693832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec444d407656'
down_revision: Union[str, None] = '8747c6dde27f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
