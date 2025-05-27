"""Add performance indices

Revision ID: 002
Revises: 001
Create Date: 2025-01-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add individual column indices
    
    # Bots table indices
    op.create_index('idx_bots_name', 'bots', ['name'])
    op.create_index('idx_bots_algorithm', 'bots', ['algorithm'])
    op.create_index('idx_bots_language', 'bots', ['language'])
    op.create_index('idx_bots_author', 'bots', ['author'])
    op.create_index('idx_bots_created_at', 'bots', ['created_at'])
    
    # Composite indices for bots
    op.create_index('idx_bots_algorithm_created', 'bots', ['algorithm', 'created_at'])
    op.create_index('idx_bots_author_created', 'bots', ['author', 'created_at'])
    op.create_index('idx_bots_name_algorithm', 'bots', ['name', 'algorithm'])
    
    # Test cases table indices
    op.create_index('idx_test_cases_name', 'test_cases', ['name'])
    op.create_index('idx_test_cases_size_category', 'test_cases', ['size_category'])
    op.create_index('idx_test_cases_difficulty', 'test_cases', ['difficulty'])
    op.create_index('idx_test_cases_created_at', 'test_cases', ['created_at'])
    
    # Composite indices for test cases
    op.create_index('idx_test_cases_category_difficulty', 'test_cases', ['size_category', 'difficulty'])
    op.create_index('idx_test_cases_size_created', 'test_cases', ['size_category', 'created_at'])
    
    # Bot submissions table indices
    op.create_index('idx_bot_submissions_bot_id', 'bot_submissions', ['bot_id'])
    op.create_index('idx_bot_submissions_submitted_at', 'bot_submissions', ['submitted_at'])
    op.create_index('idx_bot_submissions_status', 'bot_submissions', ['status'])
    op.create_index('idx_bot_submissions_total_score', 'bot_submissions', ['total_score'])
    
    # Composite indices for bot submissions (critical for leaderboard performance)
    op.create_index('idx_submissions_bot_status', 'bot_submissions', ['bot_id', 'status'])
    op.create_index('idx_submissions_status_score', 'bot_submissions', ['status', 'total_score'])
    op.create_index('idx_submissions_bot_submitted', 'bot_submissions', ['bot_id', 'submitted_at'])
    op.create_index('idx_submissions_score_submitted', 'bot_submissions', ['total_score', 'submitted_at'])
    
    # Partial index for completed submissions (most common leaderboard query)
    op.execute("""
        CREATE INDEX idx_submissions_completed_score 
        ON bot_submissions (total_score) 
        WHERE status = 'completed'
    """)
    
    # Bot results table indices
    op.create_index('idx_bot_results_submission_id', 'bot_results', ['submission_id'])
    op.create_index('idx_bot_results_test_case_id', 'bot_results', ['test_case_id'])
    op.create_index('idx_bot_results_execution_time', 'bot_results', ['execution_time'])
    op.create_index('idx_bot_results_memory_usage', 'bot_results', ['memory_usage'])
    op.create_index('idx_bot_results_success', 'bot_results', ['success'])
    op.create_index('idx_bot_results_created_at', 'bot_results', ['created_at'])
    
    # Composite indices for bot results (critical for analytics)
    op.create_index('idx_results_submission_success', 'bot_results', ['submission_id', 'success'])
    op.create_index('idx_results_submission_test_case', 'bot_results', ['submission_id', 'test_case_id'])
    op.create_index('idx_results_test_case_success_time', 'bot_results', ['test_case_id', 'success', 'execution_time'])
    op.create_index('idx_results_success_time', 'bot_results', ['success', 'execution_time'])
    op.create_index('idx_results_created_success', 'bot_results', ['created_at', 'success'])
    
    # Partial indices for successful results only (most common for performance analysis)
    op.execute("""
        CREATE INDEX idx_results_successful_time 
        ON bot_results (execution_time) 
        WHERE success = 'pass'
    """)
    
    op.execute("""
        CREATE INDEX idx_results_successful_memory 
        ON bot_results (memory_usage) 
        WHERE success = 'pass'
    """)
    
    # Add unique constraint to prevent duplicate results for same submission+test_case
    op.create_index('idx_results_unique_submission_test', 'bot_results', 
                   ['submission_id', 'test_case_id'], unique=True)


def downgrade() -> None:
    # Drop all the indices in reverse order
    
    # Unique constraint
    op.drop_index('idx_results_unique_submission_test', table_name='bot_results')
    
    # Partial indices
    op.execute("DROP INDEX IF EXISTS idx_results_successful_memory")
    op.execute("DROP INDEX IF EXISTS idx_results_successful_time")
    op.execute("DROP INDEX IF EXISTS idx_submissions_completed_score")
    
    # Bot results composite indices
    op.drop_index('idx_results_created_success', table_name='bot_results')
    op.drop_index('idx_results_success_time', table_name='bot_results')
    op.drop_index('idx_results_test_case_success_time', table_name='bot_results')
    op.drop_index('idx_results_submission_test_case', table_name='bot_results')
    op.drop_index('idx_results_submission_success', table_name='bot_results')
    
    # Bot results individual indices
    op.drop_index('idx_bot_results_created_at', table_name='bot_results')
    op.drop_index('idx_bot_results_success', table_name='bot_results')
    op.drop_index('idx_bot_results_memory_usage', table_name='bot_results')
    op.drop_index('idx_bot_results_execution_time', table_name='bot_results')
    op.drop_index('idx_bot_results_test_case_id', table_name='bot_results')
    op.drop_index('idx_bot_results_submission_id', table_name='bot_results')
    
    # Bot submissions composite indices
    op.drop_index('idx_submissions_score_submitted', table_name='bot_submissions')
    op.drop_index('idx_submissions_bot_submitted', table_name='bot_submissions')
    op.drop_index('idx_submissions_status_score', table_name='bot_submissions')
    op.drop_index('idx_submissions_bot_status', table_name='bot_submissions')
    
    # Bot submissions individual indices
    op.drop_index('idx_bot_submissions_total_score', table_name='bot_submissions')
    op.drop_index('idx_bot_submissions_status', table_name='bot_submissions')
    op.drop_index('idx_bot_submissions_submitted_at', table_name='bot_submissions')
    op.drop_index('idx_bot_submissions_bot_id', table_name='bot_submissions')
    
    # Test cases composite indices
    op.drop_index('idx_test_cases_size_created', table_name='test_cases')
    op.drop_index('idx_test_cases_category_difficulty', table_name='test_cases')
    
    # Test cases individual indices
    op.drop_index('idx_test_cases_created_at', table_name='test_cases')
    op.drop_index('idx_test_cases_difficulty', table_name='test_cases')
    op.drop_index('idx_test_cases_size_category', table_name='test_cases')
    op.drop_index('idx_test_cases_name', table_name='test_cases')
    
    # Bots composite indices
    op.drop_index('idx_bots_name_algorithm', table_name='bots')
    op.drop_index('idx_bots_author_created', table_name='bots')
    op.drop_index('idx_bots_algorithm_created', table_name='bots')
    
    # Bots individual indices
    op.drop_index('idx_bots_created_at', table_name='bots')
    op.drop_index('idx_bots_author', table_name='bots')
    op.drop_index('idx_bots_language', table_name='bots')
    op.drop_index('idx_bots_algorithm', table_name='bots')
    op.drop_index('idx_bots_name', table_name='bots')