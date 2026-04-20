"""Add solution_likes table

Revision ID: 004_add_solution_likes
Revises: 003_add_solutions
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_solution_likes'
down_revision = '003_add_solutions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'solution_likes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('solution_id', sa.Integer(), sa.ForeignKey('solutions.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint('unique_user_solution_like', 'solution_likes', ['user_id', 'solution_id'])


def downgrade():
    op.drop_table('solution_likes')