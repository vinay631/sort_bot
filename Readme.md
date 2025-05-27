# Sort Bot Leaderboard API

A competitive platform for sorting algorithm bots built with FastAPI, PostgreSQL, and SQLAlchemy.

## Features

- **Bot Management**: Create and store sorting algorithm implementations
- **Performance Testing**: Evaluate bots against various test cases with different array sizes and patterns
- **Leaderboard**: Rank bots by performance (execution time)
- **Background Processing**: Asynchronous bot evaluation with timeout protection
- **Database Migration**: Alembic for schema versioning
- **Docker Support**: Easy deployment with Docker Compose

## Architecture

### Database Schema

- **Bots**: Store bot code, metadata, and authorship info
- **Test Cases**: Store input arrays and expected outputs for different scenarios
- **Bot Submissions**: Track evaluation runs with status and scores
- **Bot Results**: Detailed results for each test case execution

### API Design

The API provides endpoints for:
- Creating and retrieving bots
- Submitting bots for evaluation
- Viewing leaderboards and detailed results
- Managing test cases

### Bot Evaluation

Bots are evaluated by:
1. Running the bot code against multiple test cases
2. Measuring execution time for each test
3. Verifying correctness of sorted output
4. Handling timeouts and errors gracefully
5. Calculating overall performance score

### Design Decisions
`FastAPI` is used as the web framework with `Postgres` as backend database with `sqlalchemy` being the ORM. `alembic` is used for data migration.

Bot submitted code runs in a asyncio created subprocess which has a default timeout of 30 seconds. The implementation for this can be found in `bot_evaluator.py` module. The current solution to run the bot submitted code is vulnerable to security attack like File system access (`open('/etc/passwd')`), Network requests (`urllib.request.urlopen()`), System commands (`os.system('rm -rf /')`) etc. A better solution would be to use a sandboxed environment using Docker, for example. In addition to this, we can also use python AST restrictions to enhance security.

We are using `Postgres` as our database of choice. Indices and partial indices have been added to the tables for optimizing common query performances. With this solution, we might be able scale the app for few hundred thousand bots, but beyond that, leaderboard queries and other analytical queries can overwhelm the database. We could have multiple read replicas but a better solution would be to use a hybrid approach with Postgres db and Redis. Postgres would be used for persisting bot metadata and Redis would be used to serve leaderboard queries using the data structure Sorted Sets which makes leaderboards simple to create and manipulate (query). 

Input validations are done using pydantic models.

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or use Docker)
- Git

### Option 1: Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd sort-bot-leaderboard
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Start PostgreSQL 
createdb sortbot_db

# Create the user with password
createuser -P sortbot

# When prompted, enter the password: sortbot
psql -c "GRANT ALL PRIVILEGES ON DATABASE sortbot_db TO sortbot;"

# Run migrations
alembic upgrade head
```

3. **Start the API**:
```bash
uvicorn main:app --reload
```

### Option 2: Docker (NOT COMPLETE!!)

1. **Start everything with Docker Compose (Not complete)**:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- FastAPI application on port 8000

### Create sample bots:
```bash
python test_bots.py
```

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs (Swagger UI, shows the request body and response)
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Bot Management

- `POST /bots` - Create a new bot
- `GET /bots` - List all bots
- `GET /bots/{bot_id}` - Get specific bot details

### Bot Evaluation

- `POST /bots/{bot_id}/submit` - Submit bot for evaluation
- `GET /submissions/{submission_id}` - Get submission status
- `GET /submissions/{submission_id}/results` - Get detailed results

### API Usage
`test_bots.py` provides an example of how to submit a bot in python. Another good source for usage is: http://localhost:8000/docs

### Leaderboard

- `GET /leaderboard` - Get top performing bots
- `GET /test-cases` - List available test cases

## Bot Code Requirements

Your bot must implement a function called `sort_array` that:
- Takes a list of integers as input
- Returns a sorted list of integers
- Completes within the timeout limit (30 seconds)

Example bot:
```python
def sort_array(arr):
    """My awesome sorting algorithm"""
    return sorted(arr)  # Using Python's built-in sort
```

## Test Cases

The system includes various test scenarios:
- **Best Case**: Already sorted arrays
- **Worst Case**: Reverse sorted arrays
- **Random**: Randomly shuffled arrays
- **Small/Medium/Large**: Different array sizes (~1K, ~10K, ~100K elements)

## Performance Scoring

Bots are ranked by:
1. **Correctness**: Must produce correctly sorted output
2. **Speed**: Average execution time across all test cases
3. **Reliability**: Successful completion without errors/timeouts

## Database Migration

### Creating new migrations:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Applying migrations:
```bash
alembic upgrade head
```

### Reverting migrations:
```bash
alembic downgrade -1
```

## Development

### Project Structure
```
sort-bot-leaderboard/
├── app/
|   ├── main.py                 # FastAPI application
|   ├── core
|       ├── bot_evaluator.py    # Bot evaluation service
|   ├── models
|       ├── pydantic_models.py # pydantic models for API request and response
|       ├── db_models.py  # Sqlalchemy db models
|   ├── utils
|       ├── load_test_cases.py # Script to load test cases 
├── requirements.txt        # Python dependencies
├── alembic.ini            # Alembic configuration
├── alembic/               # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── load_test_data.py      # Script to load test cases 
├── test_bots.py           # Sample bot implementations
├── docker-compose.yml     # Docker setup
├── Dockerfile            # Container definition
└── README.md
```

### Adding New Features

1. **Database Changes**: Create migration with `alembic revision --autogenerate`
2. **API Changes**: Update models in `main.py` and test endpoints
3. **Bot Evaluation**: Modify `BotEvaluator` class for new test scenarios

### Testing

```bash
pytest tests/
```

## Stretch Goals Implemented

- ✅ Handle bots that hang (timeout protection)
- ✅ Filtering/Sorting of Leaderboard
- ✅ Allow uploading or adding custom input arrays
