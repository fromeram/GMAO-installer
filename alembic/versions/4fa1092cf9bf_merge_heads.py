"""merge heads

Revision ID: 4fa1092cf9bf
Revises: 1efbcbefaf11, 8a72fb27622a
Create Date: 2025-05-17 20:03:29.139289

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '4fa1092cf9bf'
down_revision = ('1efbcbefaf11', '8a72fb27622a')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass