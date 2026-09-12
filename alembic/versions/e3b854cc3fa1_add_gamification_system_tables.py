"""Add gamification system tables

Revision ID: e3b854cc3fa1
Revises: 91e85f4a7a37
Create Date: 2025-05-26 20:30:47.626748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision: str = 'e3b854cc3fa1'
down_revision: Union[str, None] = '91e85f4a7a37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Crear ENUMs primero
    #achievementtype_enum = postgresql.ENUM('SPEED', 'QUALITY', 'CONSISTENCY', 'LEARNING', 'TEAMWORK', 'INNOVATION', name='achievementtype')
    #achievementtype_enum.create(op.get_bind(), checkfirst=True)
    
    #badgerarity_enum = postgresql.ENUM('COMMON', 'RARE', 'EPIC', 'LEGENDARY', name='badgerarity')
    #badgerarity_enum.create(op.get_bind(), checkfirst=True)
    
    # Crear tabla achievements
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('SPEED', 'QUALITY', 'CONSISTENCY', 'LEARNING', 'TEAMWORK', 'INNOVATION', name='achievementtype'), nullable=False),
        sa.Column('rarity', sa.Enum('COMMON', 'RARE', 'EPIC', 'LEGENDARY', name='badgerarity'), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=False),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('condition_json', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
    
    # Crear tabla user_points
    op.create_table('user_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=True, default=0),
        sa.Column('weekly_points', sa.Integer(), nullable=True, default=0),
        sa.Column('monthly_points', sa.Integer(), nullable=True, default=0),
        sa.Column('current_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('best_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('level', sa.Integer(), nullable=True, default=1),
        sa.Column('experience', sa.Integer(), nullable=True, default=0),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_points_id'), 'user_points', ['id'], unique=False)
    
    # Crear tabla point_transactions
    op.create_table('point_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_points_id', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=200), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('multiplier', sa.Float(), nullable=True, default=1.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_points_id'], ['user_points.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_point_transactions_id'), 'point_transactions', ['id'], unique=False)
    
    # Crear tabla user_achievements
    op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True, default=100),
        sa.Column('notified', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
    
    # Crear tabla challenges  
    op.create_table('challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('SPEED', 'QUALITY', 'CONSISTENCY', 'LEARNING', 'TEAMWORK', 'INNOVATION', name='achievementtype'), nullable=False),
        sa.Column('points_reward', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('condition_json', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_challenges_id'), 'challenges', ['id'], unique=False)
    
    # Crear tabla challenge_participations
    op.create_table('challenge_participations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_progress', sa.Integer(), nullable=True, default=0),
        sa.Column('completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_challenge_participations_id'), 'challenge_participations', ['id'], unique=False)

def downgrade():
    # Eliminar tablas en orden inverso
    op.drop_index(op.f('ix_challenge_participations_id'), table_name='challenge_participations')
    op.drop_table('challenge_participations')
    op.drop_index(op.f('ix_challenges_id'), table_name='challenges')
    op.drop_table('challenges')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_index(op.f('ix_point_transactions_id'), table_name='point_transactions')
    op.drop_table('point_transactions')
    op.drop_index(op.f('ix_user_points_id'), table_name='user_points')
    op.drop_table('user_points')
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')
    
    # Eliminar ENUMs
    postgresql.ENUM(name='badgerarity').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='achievementtype').drop(op.get_bind(), checkfirst=True)