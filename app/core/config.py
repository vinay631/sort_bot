from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://sortbot:sortbot@localhost:5432/sortbot_db"
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Sort Bot Leaderboard API"
    app_version: str = "1.0.0"
    
    # Bot Execution
    bot_timeout: int = 30  # seconds
    max_memory_mb: int = 128  # MB
    sandbox_enabled: bool = True
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"

settings = Settings()
