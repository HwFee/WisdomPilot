"""Add solutions table

Revision ID: 003_add_solutions
Revises:
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_solutions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'solutions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('problem_link', sa.String(500), nullable=True),
        sa.Column('tags', sa.JSON(), server_default='[]'),
        sa.Column('is_pinned', sa.Boolean(), server_default='0'),
        sa.Column('is_announcement', sa.Boolean(), server_default='0'),
        sa.Column('view_count', sa.Integer(), server_default='0'),
        sa.Column('like_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('solutions')
