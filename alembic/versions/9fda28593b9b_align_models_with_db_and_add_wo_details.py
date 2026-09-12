"""Align models with DB and add WO details (EDITED)

Revision ID: 9fda28593b9b
Revises:
Create Date: 2025-04-19 15:03:41.937606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# Quitamos import innecesario de postgresql si no se usa abajo
# from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9fda28593b9b'
down_revision: Union[str, None] = None # Al ser la primera migración real ahora, no hay down_revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Comandos Mantenidos: Crear nuevas tablas ###
    op.create_table('cause_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    # Creamos explícitamente el índice si el modelo lo tiene (o Alembic lo sugiere)
    op.create_index(op.f('ix_cause_codes_id'), 'cause_codes', ['id'], unique=False)

    op.create_table('failure_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_failure_codes_id'), 'failure_codes', ['id'], unique=False)

    op.create_table('remedy_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_remedy_codes_id'), 'remedy_codes', ['id'], unique=False)

    # --- Comandos Mantenidos: Añadir columnas y FKs a work_orders ---
    op.add_column('work_orders', sa.Column('failure_code_id', sa.Integer(), nullable=True))
    op.add_column('work_orders', sa.Column('cause_code_id', sa.Integer(), nullable=True))
    op.add_column('work_orders', sa.Column('remedy_code_id', sa.Integer(), nullable=True))
    op.add_column('work_orders', sa.Column('actual_start_time', sa.DateTime(), nullable=True))
    op.add_column('work_orders', sa.Column('actual_end_time', sa.DateTime(), nullable=True))
    op.add_column('work_orders', sa.Column('downtime_hours', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('work_orders', sa.Column('completion_notes', sa.Text(), nullable=True))

    # Se crean las FKs explícitamente
    # Usamos nombres explícitos para las constraints para mejor control (opcional pero recomendado)
    op.create_foreign_key('fk_work_orders_failure_code', 'work_orders', 'failure_codes', ['failure_code_id'], ['id'])
    op.create_foreign_key('fk_work_orders_cause_code', 'work_orders', 'cause_codes', ['cause_code_id'], ['id'])
    op.create_foreign_key('fk_work_orders_remedy_code', 'work_orders', 'remedy_codes', ['remedy_code_id'], ['id'])

    # ### Comandos Eliminados/Comentados (Ajustes no esenciales ahora) ###
    # op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    # op.alter_column('inventory', 'price', ...) # Dejamos la DB como está por ahora
    # op.alter_column('lines', 'section_id', ...)
    # op.alter_column('machines', 'modelo', ...)
    # ... (TODOS los otros op.alter_column, op.create_index, op.drop_constraint, etc. para tablas existentes) ...
    # op.alter_column('work_orders', 'details', ...) # Eliminado porque corregimos el modelo
    # op.alter_column('work_orders', 'imagen_url', ...) # Eliminado porque corregimos el modelo
    # op.create_index(op.f('ix_work_orders_id'), 'work_orders', ['id'], unique=False) # El índice PK ya existe

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Comandos auto generados - ¡AJUSTAR MANUALMENTE SI ES NECESARIO! ###
    # Asegúrate que el downgrade revierte SÓLO lo que hiciste en upgrade

    # Eliminar FKs primero
    op.drop_constraint('fk_work_orders_remedy_code', 'work_orders', type_='foreignkey')
    op.drop_constraint('fk_work_orders_cause_code', 'work_orders', type_='foreignkey')
    op.drop_constraint('fk_work_orders_failure_code', 'work_orders', type_='foreignkey')

    # Eliminar columnas añadidas
    op.drop_column('work_orders', 'completion_notes')
    op.drop_column('work_orders', 'downtime_hours')
    op.drop_column('work_orders', 'actual_end_time')
    op.drop_column('work_orders', 'actual_start_time')
    op.drop_column('work_orders', 'remedy_code_id')
    op.drop_column('work_orders', 'cause_code_id')
    op.drop_column('work_orders', 'failure_code_id')

    # Eliminar índices y tablas nuevas
    op.drop_index(op.f('ix_remedy_codes_id'), table_name='remedy_codes')
    op.drop_table('remedy_codes')
    op.drop_index(op.f('ix_failure_codes_id'), table_name='failure_codes')
    op.drop_table('failure_codes')
    op.drop_index(op.f('ix_cause_codes_id'), table_name='cause_codes')
    op.drop_table('cause_codes')

    # ### Comandos de Downgrade eliminados (porque eliminamos sus upgrades) ###
    # op.alter_column(...)
    # op.create_index(...)
    # op.drop_constraint(...)
    # ...etc...

    # ### end Alembic commands ###