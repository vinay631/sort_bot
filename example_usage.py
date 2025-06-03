import httpx
import asyncio

# Selection Sort Bot
SELECTION_SORT_BOT = """
def sort_array(arr):
    '''Selection sort implementation'''
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
"""

BOT_PAYLOAD = {
            "name": "Selection Sort Bot",
            "description": "Simple O(n²) selection sort implementation",
            "algorithm": "selection_sort",
            "code": SELECTION_SORT_BOT,
            "author": "Test User"
        }

BASE_URL = "http://localhost:8000"
async def create_bot():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/bots", json=BOT_PAYLOAD)
        if response.status_code == 200:
            print("Bot created successfully:", response.json())

            bot = response.json()
            print(f"Created bot: {bot['name']} (ID: {bot['id']})")
                        
            # Submit bot for evaluation
            submit_response = await client.post(f"{BASE_URL}/bots/{bot['id']}/submit")
            if submit_response.status_code == 200:
                submission = submit_response.json()
                print(f"Submitted bot for evaluation: {submission['submission_id']}")
            else:
                print(f"Failed to submit bot: {submit_response.text}")
        else:
            print("Failed to create bot:", response.status_code, response.text)

        leaderboard_response = await client.get(f"{BASE_URL}/leaderboard")
        if leaderboard_response.status_code == 200:
            leaderboard = leaderboard_response.json()
            print("Leaderboard:", leaderboard)
        else:
            print("Failed to fetch leaderboard:", leaderboard_response.status_code, leaderboard_response.text)

        
