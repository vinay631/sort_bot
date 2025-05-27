# Sort Bot Leaderboard API
# A FastAPI-based backend for managing and evaluating sorting bot submissions

import asyncio
import json
import logging
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any
import signal
import subprocess
import tempfile
import os

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter

from app.core.bot_evaluator import BotEvaluator
from app.utils.load_test_cases import load_initial_test_cases

from app.models.pydantic_models import (
    BotCreate, BotResponse, SubmissionResponse, LeaderboardEntry, BotResultResponse
)
from app.models.db_models import Bot, TestCase, BotSubmission, BotResult


# Configure logging
# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('sortbot.log')  # File output
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sortbot:sortbot@localhost:5432/sortbot_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize evaluator
evaluator = BotEvaluator()


# Create FastAPI app
app = FastAPI(
    title="Sort Bot Leaderboard API",
    description="A competitive platform for sorting algorithm bots",
    version="1.0.0"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load test cases from input files

# API Routes
v1_router = APIRouter(prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Sort Bot Leaderboard API", "version": "1.0.0"}

@app.post("/bots", response_model=BotResponse)
async def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Create a new bot"""
    db_bot = Bot(**bot.dict())
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)

    return BotResponse(
        id=str(db_bot.id),
        name=db_bot.name,
        description=db_bot.description,
        algorithm=db_bot.algorithm,
        language=db_bot.language,
        author=db_bot.author,
        created_at=db_bot.created_at
    )

@app.get("/bots", response_model=List[BotResponse])
async def list_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all bots"""
    bots = db.query(Bot).offset(skip).limit(limit).all()
    return bots

@app.get("/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get a specific bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@app.post("/bots/{bot_id}/submit")
async def submit_bot(
    bot_id: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit a bot for evaluation"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Create submission record
    submission = BotSubmission(
        bot_id=bot_id,
        status="pending"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Get all test cases
    test_cases = db.query(TestCase).all()
    
    # Schedule background evaluation
    background_tasks.add_task(
        run_bot_evaluation, 
        bot.code, 
        test_cases, 
        str(submission.id)
    )
    
    return {"submission_id": str(submission.id), "status": "pending"}

async def run_bot_evaluation(bot_code: str, test_cases: List[TestCase], submission_id: str):
    """Background task for running bot evaluation"""
    db = SessionLocal()
    try:
        # Update submission status
        submission = db.query(BotSubmission).filter(BotSubmission.id == submission_id).first()
        submission.status = "running"
        db.commit()
        
        # Run evaluation
        await evaluator.evaluate_bot(bot_code, test_cases, submission_id, db)
        
    except Exception as e:
        logging.error(f"Error in bot evaluation: {str(e)}")
        # Mark submission as failed
        submission = db.query(BotSubmission).filter(BotSubmission.id == submission_id).first()
        if submission:
            submission.status = "failed"
            db.commit()
    finally:
        db.close()

@app.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: str, db: Session = Depends(get_db)):
    """Get submission details"""
    submission = db.query(BotSubmission).join(Bot).filter(BotSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return SubmissionResponse(
        id=str(submission.id),
        bot_id=str(submission.bot_id),
        bot_name=submission.bot.name,
        submitted_at=submission.submitted_at,
        status=submission.status,
        total_score=submission.total_score
    )

@app.get("/submissions/{submission_id}/results", response_model=List[BotResultResponse])
async def get_submission_results(submission_id: str, db: Session = Depends(get_db)):
    """Get detailed results for a submission"""
    submission = db.query(BotSubmission).filter(BotSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    results = db.query(BotResult).join(TestCase).filter(BotResult.submission_id == submission_id).all()
    
    return [
        BotResultResponse(
            test_case_name=result.test_case.name,
            size_category=result.test_case.size_category,
            execution_time=result.execution_time,
            success=result.success,
            error_message=result.error_message
        )
        for result in results
    ]

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    size_category: Optional[str] = None,
    algorithm: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get the leaderboard of best performing bots"""
    
    base_query = db.query(
        BotSubmission.id.label('submission_id'),
        BotSubmission.total_score,
        BotSubmission.submitted_at,
        Bot.id.label('bot_id'),
        Bot.name.label('bot_name'),
        Bot.algorithm,
        Bot.author
    ).join(Bot).filter(
        BotSubmission.status == "completed",
        BotSubmission.total_score.isnot(None)
    )
    
    # Add algorithm filter if specified (uses idx_bots_algorithm)
    if algorithm:
        base_query = base_query.filter(Bot.algorithm == algorithm)
    
    # Add size category filter if specified
    if size_category:
        # Subquery to get submissions that have results for the specified size category
        size_subquery = db.query(BotSubmission.id).join(BotResult).join(TestCase).filter(
            TestCase.size_category == size_category,  # Uses idx_test_cases_size_category
            BotResult.success == "pass"  # Uses idx_results_success_time partial index
        ).subquery()
        
        base_query = base_query.filter(BotSubmission.id.in_(size_subquery))
    
    # Order by score and apply pagination (uses idx_submissions_status_score)
    submissions = base_query.order_by(BotSubmission.total_score.asc()).offset(offset).limit(limit).all()
    
    leaderboard = []
    for rank, submission in enumerate(submissions, start=offset + 1):
        leaderboard.append(LeaderboardEntry(
            rank=rank,
            bot_name=submission.bot_name,
            bot_id=str(submission.bot_id),
            algorithm=submission.algorithm,
            author=submission.author,
            total_score=submission.total_score,
            submission_id=str(submission.submission_id),
            submitted_at=submission.submitted_at
        ))
    
    return leaderboard

@app.get("/test-cases")
async def get_test_cases(db: Session = Depends(get_db)):
    """Get all test cases"""
    test_cases = db.query(TestCase).all()
    return [
        {
            "id": tc.id,
            "name": tc.name,
            "size_category": tc.size_category,
            "difficulty": tc.difficulty,
            "data_length": len(tc.data)
        }
        for tc in test_cases
    ]

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)