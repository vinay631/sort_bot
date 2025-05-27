"""
Sample bot implementations for testing the Sort Bot Leaderboard API
"""

# Simple Bubble Sort Bot
BUBBLE_SORT_BOT = """
def sort_array(arr):
    '''Bubble sort implementation'''
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""

# Quick Sort Bot
QUICK_SORT_BOT = """
def sort_array(arr):
    '''Quick sort implementation'''
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return sort_array(left) + middle + sort_array(right)
"""

# Merge Sort Bot
MERGE_SORT_BOT = """
def sort_array(arr):
    '''Merge sort implementation'''
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = sort_array(arr[:mid])
    right = sort_array(arr[mid:])
    
    result = []
    i, j = 0, 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""

# Python Built-in Sort Bot (should be fastest)
BUILTIN_SORT_BOT = """
def sort_array(arr):
    '''Using Python's built-in sorted function'''
    return sorted(arr)
"""

# Insertion Sort Bot
INSERTION_SORT_BOT = """
def sort_array(arr):
    '''Insertion sort implementation'''
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
"""

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

# Broken Bot (for testing error handling)
BROKEN_BOT = """
def sort_array(arr):
    '''This bot will intentionally fail'''
    return arr[1000000]  # Index error
"""

# Infinite Loop Bot (for testing timeout handling)
INFINITE_LOOP_BOT = """
def sort_array(arr):
    '''This bot will run forever'''
    while True:
        pass
    return arr
"""

# Test script to create sample bots
if __name__ == "__main__":
    import httpx
    import asyncio
    
    # Sample bots to create
    sample_bots = [
        {
            "name": "Bubble Sort Bot",
            "description": "Simple O(n²) bubble sort implementation",
            "algorithm": "bubble_sort",
            "code": BUBBLE_SORT_BOT,
            "author": "Test User"
        },
        {
            "name": "Quick Sort Bot", 
            "description": "Efficient O(n log n) quicksort implementation",
            "algorithm": "quick_sort",
            "code": QUICK_SORT_BOT,
            "author": "Test User"
        },
        {
            "name": "Merge Sort Bot",
            "description": "Stable O(n log n) merge sort implementation", 
            "algorithm": "merge_sort",
            "code": MERGE_SORT_BOT,
            "author": "Test User"
        },
        {
            "name": "Built-in Sort Bot",
            "description": "Using Python's highly optimized built-in sort",
            "algorithm": "timsort",
            "code": BUILTIN_SORT_BOT,
            "author": "Test User"
        },
        {
            "name": "Insertion Sort Bot",
            "description": "Simple O(n²) insertion sort, good for small arrays",
            "algorithm": "insertion_sort", 
            "code": INSERTION_SORT_BOT,
            "author": "Test User"
        },
        {
            "name": "Selection Sort Bot",
            "description": "Simple O(n²) selection sort implementation",
            "algorithm": "selection_sort",
            "code": SELECTION_SORT_BOT,
            "author": "Test User"
        }
    ]
    
    async def create_and_submit_bots():
        async with httpx.AsyncClient() as client:
            base_url = "http://localhost:8000"
            
            for bot_data in sample_bots:
                try:
                    # Create bot
                    response = await client.post(f"{base_url}/bots", json=bot_data)
                    if response.status_code == 200:
                        bot = response.json()
                        print(f"Created bot: {bot['name']} (ID: {bot['id']})")
                        
                        # Submit bot for evaluation
                        submit_response = await client.post(f"{base_url}/bots/{bot['id']}/submit")
                        if submit_response.status_code == 200:
                            submission = submit_response.json()
                            print(f"Submitted bot for evaluation: {submission['submission_id']}")
                        else:
                            print(f"Failed to submit bot: {submit_response.text}")
                    else:
                        print(f"Failed to create bot {bot_data['name']}: {response.text}")
                        
                except Exception as e:
                    print(f"Error with bot {bot_data['name']}: {e}")
    
    print("Creating and submitting sample bots...")
    asyncio.run(create_and_submit_bots())
    print("Done! Check the leaderboard at http://localhost:8000/leaderboard")