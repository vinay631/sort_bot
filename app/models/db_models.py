import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Index, func
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sortbot:sortbot@localhost:5432/sortbot_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models with proper indexing
from sqlalchemy import Index

class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)  # Index for searching by name
    description = Column(Text)
    algorithm = Column(String(100), index=True)  # Index for filtering by algorithm
    code = Column(Text, nullable=False)  # The actual bot code
    language = Column(String(50), default="python", index=True)  # Index for language filtering
    author = Column(String(255), index=True)  # Index for author searches
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Index for date sorting
    
    # Relationships
    submissions = relationship("BotSubmission", back_populates="bot")
    
    # Composite indices for common query patterns
    __table_args__ = (
        Index('idx_bots_algorithm_created', 'algorithm', 'created_at'),  # Algorithm leaderboards by date
        Index('idx_bots_author_created', 'author', 'created_at'),  # Author's bots by date
        Index('idx_bots_name_algorithm', 'name', 'algorithm'),  # Search by name and algorithm
    )

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Index for test case lookup
    size_category = Column(String(50), nullable=False, index=True)  # Index for category filtering
    data = Column(JSON, nullable=False)  # The array to sort
    expected_result = Column(JSON, nullable=False)  # Expected sorted array
    difficulty = Column(String(50), index=True)  # Index for difficulty filtering
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    results = relationship("BotResult", back_populates="test_case")
    
    # Composite indices
    __table_args__ = (
        Index('idx_test_cases_category_difficulty', 'size_category', 'difficulty'),  # Filter by category and difficulty
        Index('idx_test_cases_size_created', 'size_category', 'created_at'),  # Category performance over time
    )

class BotSubmission(Base):
    __tablename__ = "bot_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)  # Index for bot's submissions
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)  # Index for chronological queries
    status = Column(String(50), default="pending", index=True)  # TODO: Use Enum for better type safety
    # Status can be 'pending', 'completed', 'failed', etc.
    total_score = Column(Float, index=True)  # Index for leaderboard sorting
    
    # Relationships
    bot = relationship("Bot", back_populates="submissions")
    results = relationship("BotResult", back_populates="submission")
    
    # Composite indices for performance-critical queries
    __table_args__ = (
        Index('idx_submissions_bot_status', 'bot_id', 'status'),  # Bot's submissions by status
        Index('idx_submissions_status_score', 'status', 'total_score'),  # Leaderboard (completed submissions by score)
        Index('idx_submissions_bot_submitted', 'bot_id', 'submitted_at'),  # Bot's submission history
        Index('idx_submissions_score_submitted', 'total_score', 'submitted_at'),  # Best scores over time
        # Partial index for completed submissions only (most common query)
        Index('idx_submissions_completed_score', 'total_score', postgresql_where=text("status = 'completed'")),
    )

class BotResult(Base):
    __tablename__ = "bot_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("bot_submissions.id"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    execution_time = Column(Float, index=True)  # Index for performance analysis
    memory_usage = Column(Float, index=True)
    success = Column(String(20), default="unknown", index=True)  # TODO: Use Enum for better type safety
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    submission = relationship("BotSubmission", back_populates="results")
    test_case = relationship("TestCase", back_populates="results")
    
    # Composite indices for complex analytics queries
    __table_args__ = (
        Index('idx_results_submission_success', 'submission_id', 'success'),  # Submission success rate
        Index('idx_results_submission_test_case', 'submission_id', 'test_case_id'),  # Unique constraint simulation
        Index('idx_results_test_case_success_time', 'test_case_id', 'success', 'execution_time'),  # Test case performance
        Index('idx_results_success_time', 'success', 'execution_time'),  # Overall performance stats
        Index('idx_results_created_success', 'created_at', 'success'),  # Success rate over time
        # Partial indices for successful results only (most common for leaderboards)
        Index('idx_results_successful_time', 'execution_time', postgresql_where=text("success = 'pass'")),
        Index('idx_results_successful_memory', 'memory_usage', postgresql_where=text("success = 'pass'")),
    )
