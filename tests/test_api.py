"""
Test suite for the Sort Bot Leaderboard API
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db, Base
import tempfile
import os

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
class TestBotAPI:
    
    async def test_root_endpoint(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_create_bot(self, client):
        bot_data = {
            "name": "Test Bot",
            "description": "A test sorting bot",
            "algorithm": "bubble_sort",
            "code": "def sort_array(arr):\n    return sorted(arr)",
            "author": "Test User"
        }
        
        response = await client.post("/bots", json=bot_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == bot_data["name"]
        assert data["algorithm"] == bot_data["algorithm"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_bot_validation(self, client):
        # Test missing required fields
        invalid_bot = {
            "name": "",  # Empty name should fail
            "code": ""   # Empty code should fail
        }
        
        response = await client.post("/bots", json=invalid_bot)
        assert response.status_code == 422
    
    async def test_list_bots(self, client):
        # First create a bot
        bot_data = {
            "name": "List Test Bot",
            "code": "def sort_array(arr): return sorted(arr)"
        }
        
        create_response = await client.post("/bots", json=bot_data)
        assert create_response.status_code == 200
        
        # Then list bots
        response = await client.get("/bots")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(bot["name"] == "List Test Bot" for bot in data)
    
    async def test_get_bot(self, client):
        # Create a bot
        bot_data = {
            "name": "Get Test Bot",
            "code": "def sort_array(arr): return sorted(arr)"
        }
        
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        # Get the bot
        response = await client.get(f"/bots/{bot_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == bot_id
        assert data["name"] == "Get Test Bot"
    
    async def test_get_nonexistent_bot(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/bots/{fake_id}")
        assert response.status_code == 404
    
    async def test_submit_bot(self, client):
        # Create a bot first
        bot_data = {
            "name": "Submit Test Bot",
            "code": "def sort_array(arr): return sorted(arr)"
        }
        
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        # Submit the bot
        response = await client.post(f"/bots/{bot_id}/submit")
        assert response.status_code == 200
        
        data = response.json()
        assert "submission_id" in data
        assert data["status"] == "pending"
    
    async def test_submit_nonexistent_bot(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(f"/bots/{fake_id}/submit")
        assert response.status_code == 404
    
    async def test_get_submission(self, client):
        # Create and submit a bot
        bot_data = {
            "name": "Submission Test Bot",
            "code": "def sort_array(arr): return sorted(arr)"
        }
        
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        submission = submit_response.json()
        submission_id = submission["submission_id"]
        
        # Get submission details
        response = await client.get(f"/submissions/{submission_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == submission_id
        assert data["bot_id"] == bot_id
        assert data["status"] in ["pending", "running", "completed", "failed"]
    
    async def test_get_leaderboard(self, client):
        response = await client.get("/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should be empty initially or contain completed submissions
        for entry in data:
            assert "rank" in entry
            assert "bot_name" in entry
            assert "total_score" in entry
    
    async def test_get_test_cases(self, client):
        response = await client.get("/test-cases")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Test cases should be loaded automatically
        if data:  # If test cases exist
            for case in data:
                assert "id" in case
                assert "name" in case
                assert "size_category" in case
                assert "difficulty" in case
                assert "data_length" in case

@pytest.mark.asyncio
class TestBotEvaluation:
    
    async def test_simple_sort_bot(self, client):
        """Test a simple working sort bot"""
        bot_data = {
            "name": "Simple Sort Bot",
            "code": """
def sort_array(arr):
    return sorted(arr)
""",
            "algorithm": "built_in_sort"
        }
        
        # Create bot
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        # Submit for evaluation
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        submission = submit_response.json()
        submission_id = submission["submission_id"]
        
        # Wait a bit for evaluation (in real tests, you'd use proper async waiting)
        await asyncio.sleep(2)
        
        # Check submission status
        status_response = await client.get(f"/submissions/{submission_id}")
        status_data = status_response.json()
        
        # Status should be completed or still running
        assert status_data["status"] in ["pending", "running", "completed"]
    
    async def test_bubble_sort_bot(self, client):
        """Test a bubble sort implementation"""
        bot_data = {
            "name": "Bubble Sort Bot",
            "code": """
def sort_array(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
""",
            "algorithm": "bubble_sort"
        }
        
        # Create and submit bot
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        assert submit_response.status_code == 200
    
    async def test_broken_bot(self, client):
        """Test error handling with a broken bot"""
        bot_data = {
            "name": "Broken Bot",
            "code": """
def sort_array(arr):
    return arr[1000000]  # This will cause an IndexError
""",
            "algorithm": "broken"
        }
        
        # Create and submit bot
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        assert submit_response.status_code == 200
        
        submission = submit_response.json()
        submission_id = submission["submission_id"]
        
        # Wait for evaluation
        await asyncio.sleep(3)
        
        # Check results
        results_response = await client.get(f"/submissions/{submission_id}/results")
        if results_response.status_code == 200:
            results = results_response.json()
            # Should have error results
            if results:
                assert any(result["success"] == "error" for result in results)

@pytest.mark.asyncio 
class TestEdgeCases:
    
    async def test_bot_with_no_sort_function(self, client):
        """Test bot that doesn't define sort_array function"""
        bot_data = {
            "name": "No Function Bot",
            "code": """
def other_function():
    return "not a sort function"
""",
        }
        
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        assert submit_response.status_code == 200
    
    async def test_bot_with_syntax_error(self, client):
        """Test bot with syntax errors"""
        bot_data = {
            "name": "Syntax Error Bot",
            "code": """
def sort_array(arr):
    return sorted(arr
    # Missing closing parenthesis
""",
        }
        
        create_response = await client.post("/bots", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        submit_response = await client.post(f"/bots/{bot_id}/submit")
        assert submit_response.status_code == 200
    
    async def test_pagination(self, client):
        """Test API pagination"""
        # Create multiple bots
        for i in range(5):
            bot_data = {
                "name": f"Pagination Bot {i}",
                "code": "def sort_array(arr): return sorted(arr)"
            }
            await client.post("/bots", json=bot_data)
        
        # Test pagination
        response = await client.get("/bots?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3
        
        # Test offset
        response = await client.get("/bots?skip=2&limit=2") 
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])