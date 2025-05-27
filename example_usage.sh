#!/bin/bash

BASE_URL="http://localhost:8000"

# Step 1: Create the bot
echo "Creating Selection Sort Bot..."
CREATE_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Selection Sort Bot",
    "description": "Simple O(n²) selection sort implementation",
    "algorithm": "selection_sort",
    "code": "def sort_array(arr):\n    \"\"\"Selection sort implementation\"\"\"\n    n = len(arr)\n    for i in range(n):\n        min_idx = i\n        for j in range(i + 1, n):\n            if arr[j] < arr[min_idx]:\n                min_idx = j\n        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n    return arr",
    "author": "Test User"
  }' \
  "${BASE_URL}/bots")

echo "Bot creation response: $CREATE_RESPONSE"

# Extract bot ID from response (requires jq for JSON parsing)
BOT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')

if [ "$BOT_ID" != "null" ] && [ -n "$BOT_ID" ]; then
    echo "Created bot with ID: $BOT_ID"
    
    # Step 2: Submit bot for evaluation
    echo "Submitting bot for evaluation..."
    SUBMIT_RESPONSE=$(curl -s -X POST \
      "${BASE_URL}/bots/${BOT_ID}/submit")
    
    echo "Submit response: $SUBMIT_RESPONSE"
    
    # Extract submission ID if needed
    SUBMISSION_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.submission_id')
    if [ "$SUBMISSION_ID" != "null" ] && [ -n "$SUBMISSION_ID" ]; then
        echo "Submitted bot for evaluation: $SUBMISSION_ID"
    fi
else
    echo "Failed to create bot or extract bot ID"
fi

# Step 3: Get leaderboard
echo "Fetching leaderboard..."
LEADERBOARD_RESPONSE=$(curl -s -X GET \
  "${BASE_URL}/leaderboard")

echo "Leaderboard: $LEADERBOARD_RESPONSE"
