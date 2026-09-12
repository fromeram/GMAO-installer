"""add_stock_minimo_to_inventory

Revision ID: 1efbcbefaf11
Revises: 8a72fb27622a
Create Date: 2025-05-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '1efbcbefaf11'
down_revision = '8a72fb27622a' 
branch_labels = None
depends_on = None


def upgrade():
    # Añadir columna stock_minimo con valor por defecto 0
    op.add_column('inventory', sa.Column('stock_minimo', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # En caso de necesitar revertir la migración
    op.drop_column('inventory', 'stock_minimo')