"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bots table
    op.create_table('bots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('algorithm', sa.String(length=100), nullable=True),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create test_cases table
    op.create_table('test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('size_category', sa.String(length=50), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('expected_result', sa.JSON(), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_cases_id'), 'test_cases', ['id'], unique=False)
    
    # Create bot_submissions table
    op.create_table('bot_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bot_results table
    op.create_table('bot_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('success', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['bot_submissions.id'], ),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('bot_results')
    op.drop_table('bot_submissions')
    op.drop_index(op.f('ix_test_cases_id'), table_name='test_cases')
    op.drop_table('test_cases')
    op.drop_table('bots')