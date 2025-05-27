from datetime import datetime
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Pydantic Models for API
class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    algorithm: Optional[str] = None
    code: str = Field(..., min_length=1)
    language: str = "python"
    author: Optional[str] = None

class BotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    algorithm: Optional[str]
    language: str
    author: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubmissionResponse(BaseModel):
    id: str
    bot_id: str
    bot_name: str
    submitted_at: datetime
    status: str
    total_score: Optional[float]
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    rank: int
    bot_name: str
    bot_id: str
    algorithm: Optional[str]
    author: Optional[str]
    total_score: float
    submission_id: str
    submitted_at: datetime

class BotResultResponse(BaseModel):
    test_case_name: str
    size_category: str
    execution_time: Optional[float]
    success: str
    error_message: Optional[str]
    
    class Config:
        from_attributes = True