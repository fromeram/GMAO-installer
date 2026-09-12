"""add_audit_trail_table

Revision ID: 91e85f4a7a37
Revises: ec444d407656
Create Date: 2025-05-24 19:25:49.596978

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '91e85f4a7a37'
down_revision: Union[str, None] = 'ec444d407656'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tabla audit_logs y sus índices"""
    
    # Crear tabla audit_logs
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('user_role', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changes_summary', sa.Text(), nullable=True),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True, server_default='MEDIUM'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear índices para optimizar consultas
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'], postgresql_using='btree')
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_logs_module', 'audit_logs', ['module'], unique=False)
    op.create_index('idx_audit_logs_severity', 'audit_logs', ['severity'], unique=False)
    
    # Índice compuesto para consultas de dashboard (ordenado por timestamp desc)
    op.create_index('idx_audit_logs_recent_activity', 'audit_logs', [sa.text('timestamp DESC'), 'severity', 'module'])
    
    # Añadir comentarios a la tabla y columnas para documentación
    op.execute("""
        COMMENT ON TABLE audit_logs IS 'Registro de auditoría de todas las acciones importantes del sistema GMAO'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.action IS 'Tipo de acción: CREATE, UPDATE, DELETE, LOGIN, etc.'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.entity_type IS 'Tipo de entidad: WorkOrder, Machine, User, etc.'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.entity_id IS 'ID de la entidad modificada'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.old_values IS 'Estado anterior del objeto (JSON)'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.new_values IS 'Nuevo estado del objeto (JSON)'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.severity IS 'Nivel de importancia: LOW, MEDIUM, HIGH, CRITICAL'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.module IS 'Módulo del sistema: maintenance, inventory, users, etc.'
    """)
    
    op.execute("""
        COMMENT ON COLUMN audit_logs.session_id IS 'ID de sesión para agrupar acciones relacionadas'
    """)


def downgrade() -> None:
    """Eliminar tabla audit_logs y sus índices"""
    
    # Eliminar índices primero
    op.drop_index('idx_audit_logs_recent_activity', table_name='audit_logs')
    op.drop_index('idx_audit_logs_severity', table_name='audit_logs')
    op.drop_index('idx_audit_logs_module', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_timestamp', table_name='audit_logs')
    
    # Eliminar tabla
    op.drop_table('audit_logs')