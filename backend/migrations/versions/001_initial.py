"""initial schema - captures all existing models

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-25

This migration captures the full database schema as of the initial Alembic setup.
For existing databases, use `alembic stamp 001_initial` to mark as current
without executing any DDL (tables already exist).
For new databases, `alembic upgrade head` will create all tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all tables for fresh databases.

    For EXISTING databases: this migration is stamped (not executed).
    Do NOT modify this function — it must match the current schema exactly.
    Future schema changes should go in NEW migration files.
    """
    # users
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('cores', sa.Integer(), nullable=True, default=0),
        sa.Column('tier', sa.String(), nullable=True, default='bronze'),
        sa.Column('stars', sa.Integer(), nullable=True, default=0),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('checkin_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('last_checkin_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # courses
    op.create_table('courses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
    )

    # chapters
    op.create_table('chapters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
    )

    # sections
    op.create_table('sections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id']),
    )

    # exercises
    op.create_table('exercises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True, default=1),
        sa.Column('starter_code', sa.String(), nullable=True),
        sa.Column('solution', sa.String(), nullable=True),
        sa.Column('test_cases', sa.String(), nullable=True),
        sa.Column('hint', sa.String(), nullable=True),
        sa.Column('exercise_type', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True, default='tk'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id']),
    )

    # achievements
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('condition_type', sa.String(), nullable=False),
        sa.Column('condition_value', sa.Integer(), nullable=False),
        sa.Column('rarity', sa.String(), nullable=True, default='common'),
        sa.PrimaryKeyConstraint('id'),
    )

    # user_achievements
    op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id']),
    )

    # challenges
    op.create_table('challenges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True, default=1),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # user_challenges
    op.create_table('user_challenges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id']),
    )

    # user_weak_points
    op.create_table('user_weak_points',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('knowledge_point', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('wrong_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_wrong_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # spaced_repetitions
    op.create_table('spaced_repetitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('knowledge_point', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('next_review_at', sa.DateTime(), nullable=True),
        sa.Column('interval_days', sa.Integer(), nullable=True, default=1),
        sa.Column('ease_factor', sa.Float(), nullable=True, default=2.5),
        sa.Column('repetition_count', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # favorites
    op.create_table('favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # notes
    op.create_table('notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # note_tags
    op.create_table('note_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id']),
    )

    # chapter_masteries
    op.create_table('chapter_masteries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('mastery_level', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_practiced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # challenge_sessions
    op.create_table('challenge_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # user_arena_profiles
    op.create_table('user_arena_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True, default=1200),
        sa.Column('wins', sa.Integer(), nullable=True, default=0),
        sa.Column('losses', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # wrong_questions
    op.create_table('wrong_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('user_answer', sa.String(), nullable=True),
        sa.Column('wrong_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # core_transactions
    op.create_table('core_transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # tier_transactions
    op.create_table('tier_transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('from_tier', sa.String(), nullable=True),
        sa.Column('to_tier', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # mastery_xp_transactions
    op.create_table('mastery_xp_transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # solutions
    op.create_table('solutions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('is_official', sa.Boolean(), nullable=True, default=False),
        sa.Column('likes_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # solution_likes
    op.create_table('solution_likes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('solution_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['solution_id'], ['solutions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # section_knowledge_points
    op.create_table('section_knowledge_points',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id']),
    )

    # section_base_questions
    op.create_table('section_base_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_point_id', sa.Integer(), nullable=True),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('options', sa.String(), nullable=True),
        sa.Column('correct_answer', sa.String(), nullable=False),
        sa.Column('explanation', sa.String(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True, default=1),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id']),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['section_knowledge_points.id']),
    )

    # knowledge_point_masteries
    op.create_table('knowledge_point_masteries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('knowledge_point', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('p_l', sa.Float(), nullable=True, default=0.0),
        sa.Column('p_t', sa.Float(), nullable=True, default=0.0),
        sa.Column('p_s', sa.Float(), nullable=True, default=0.1),
        sa.Column('p_g', sa.Float(), nullable=True, default=0.2),
        sa.Column('total_attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('correct_attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('last_practiced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # answer_histories
    op.create_table('answer_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('user_answer', sa.String(), nullable=True),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # section_masteries
    op.create_table('section_masteries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('mastery_level', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_practiced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # course_masteries
    op.create_table('course_masteries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('mastery_level', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_practiced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # mastery_exercise_progress
    op.create_table('mastery_exercise_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, default='not_started'),
        sa.Column('attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('best_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # arena_exercise_progress
    op.create_table('arena_exercise_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=True, default=False),
        sa.Column('attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # ai_hint_caches
    op.create_table('ai_hint_caches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('hint_type', sa.String(), nullable=False),
        sa.Column('hint_content', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # chapter_progress (legacy)
    op.create_table('chapter_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('progress', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # learning_sessions
    op.create_table('learning_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # activity_logs
    op.create_table('activity_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # stats (user statistics)
    op.create_table('stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('total_exercises', sa.Integer(), nullable=True, default=0),
        sa.Column('correct_exercises', sa.Integer(), nullable=True, default=0),
        sa.Column('total_study_time', sa.Integer(), nullable=True, default=0),
        sa.Column('streak_days', sa.Integer(), nullable=True, default=0),
        sa.Column('last_study_date', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )


def downgrade() -> None:
    """Not supported — do not downgrade the initial schema."""
    pass
