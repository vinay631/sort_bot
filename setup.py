#!/usr/bin/env python3
"""
Setup script for Sort Bot Leaderboard API
Handles database initialization and test data loading
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "psycopg2", "alembic", "pydantic"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def setup_database():
    """Initialize database with Alembic migrations"""
    print("🗄️  Setting up database...")
    
    # Check if alembic is initialized
    if not Path("alembic").exists():
        print("❌ Alembic not initialized. Run 'alembic init alembic' first")
        return False
    
    # Run migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        return False
    
    return True

def load_test_data():
    """Load test cases from input files"""
    print("📊 Loading test data...")
    
    if not run_command("python load_test_data.py", "Loading test cases"):
        return False
    
    return True

def create_sample_bots():
    """Create sample bots for testing"""
    print("🤖 Creating sample bots...")
    
    # Check if API is running by trying to create bots
    try:
        # Start API in background for testing
        print("   Starting API server for bot creation...")
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        import time
        time.sleep(3)
        
        # Create sample bots
        result = run_command("python test_bots.py", "Creating sample bots")
        
        # Stop the API server
        api_process.terminate()
        api_process.wait()
        
        return result
        
    except Exception as e:
        print(f"❌ Error creating sample bots: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Sort Bot Leaderboard API Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ main.py not found. Please run this script from the project root.")
        return 1
    
    # Step 1: Check dependencies
    if not check_dependencies():
        return 1
    
    # Step 2: Setup database
    if not setup_database():
        return 1
    
    # Step 3: Load test data
    if not load_test_data():
        print("⚠️  Warning: Could not load test data, but continuing...")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the API server:")
    print("   uvicorn app.main:app --reload")
    print("\n2. Visit the API documentation:")
    print("   http://localhost:8000/docs")
    print("\n3. Create and test bots:")
    print("   python test_bots.py")
    print("\n4. View the leaderboard:")
    print("   http://localhost:8000/leaderboard")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())