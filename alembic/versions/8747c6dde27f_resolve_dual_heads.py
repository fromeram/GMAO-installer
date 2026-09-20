"""resolve_dual_heads

Revision ID: 8747c6dde27f
Revises: 4fa1092cf9bf, 560c85bf6f60
Create Date: 2025-05-24 13:56:16.668478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8747c6dde27f'
down_revision: Union[str, None] = ('4fa1092cf9bf', '560c85bf6f60')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
