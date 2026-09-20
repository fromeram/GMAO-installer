
"""add maintenance columns

Revision ID: new_maintenance_columns
Revises: 140446e9304d
Create Date: 2025-02-08 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'new_maintenance_columns'
down_revision = '140446e9304d'
branch_labels = None
depends_on = None

def upgrade():
    # Agregar columnas a la tabla existente
    op.execute("""
    DO $$
    BEGIN
        BEGIN
            ALTER TABLE maintenances 
            ADD COLUMN assigned_user_id INTEGER REFERENCES users(id),
            ADD COLUMN assigned_role_id INTEGER REFERENCES roles(id),
            ADD COLUMN is_completed BOOLEAN DEFAULT false,
            ADD COLUMN frequency VARCHAR,
            ADD COLUMN notification_interval INTEGER,
            ADD COLUMN next_maintenance_date TIMESTAMP,
            ADD COLUMN last_maintenance_date TIMESTAMP;
        EXCEPTION
            WHEN duplicate_column THEN
                NULL;
        END;
    END $$;
    """)

def downgrade():
    # Eliminar columnas en orden inverso
    op.execute("""
    DO $$
    BEGIN
        BEGIN
            ALTER TABLE maintenances 
            DROP COLUMN IF EXISTS last_maintenance_date,
            DROP COLUMN IF EXISTS next_maintenance_date,
            DROP COLUMN IF EXISTS notification_interval,
            DROP COLUMN IF EXISTS frequency,
            DROP COLUMN IF EXISTS is_completed,
            DROP COLUMN IF EXISTS assigned_role_id,
            DROP COLUMN IF EXISTS assigned_user_id;
        EXCEPTION
            WHEN undefined_column THEN
                NULL;
        END;
    END $$;
    """)
