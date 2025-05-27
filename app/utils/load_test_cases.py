from app.models.db_models import TestCase

async def load_initial_test_cases(db):
    """Load test cases from the small input file and create sample cases"""
    
    # Check if test cases already exist
    existing_count = db.query(TestCase).count()
    if existing_count > 0:
        return
    
    try:
        # Try to load from the provided input file
        from load_test_data import parse_input_file
        
        # Load arrays from inputs_small.txt
        small_arrays = parse_input_file('inputs_small.txt')
        
        if small_arrays:
            print(f"Loading {len(small_arrays)} test cases from inputs_small.txt")
            
            for i, array in enumerate(small_arrays):
                expected = sorted(array)
                
                # Determine difficulty based on array characteristics
                if array == expected:
                    difficulty = "best_case"
                elif array == sorted(array, reverse=True):
                    difficulty = "worst_case"
                else:
                    difficulty = "random"
                
                # Determine name based on characteristics
                if i == 0:
                    name = "Already Sorted (1000 elements)"
                elif i == 1:
                    name = "Reverse Sorted (1000 elements)"
                elif len(array) < 200:
                    name = f"Small Mixed Array ({len(array)} elements)"
                else:
                    name = f"Test Case {i+1} ({len(array)} elements)"
                
                test_case = TestCase(
                    name=name,
                    size_category="small",
                    data=array,
                    expected_result=expected,
                    difficulty=difficulty
                )
                db.add(test_case)
            
            db.commit()
            print(f"Successfully loaded {len(small_arrays)} test cases")
            return
            
    except Exception as e:
        print(f"Could not load from input files: {e}")
    
    # Fallback: Create sample test cases
    print("Creating sample test cases...")
    
    sample_cases = [
        {
            "name": "Small Sorted Array",
            "size_category": "small",
            "data": list(range(100)),
            "difficulty": "best_case"
        },
        {
            "name": "Small Reverse Array", 
            "size_category": "small",
            "data": list(range(100, 0, -1)),
            "difficulty": "worst_case"
        },
        {
            "name": "Small Random Array",
            "size_category": "small", 
            "data": [64, 34, 25, 12, 22, 11, 90, 5, 77, 30, 88, 76, 50, 42, 13, 27, 96, 4, 47, 82],
            "difficulty": "random"
        },
        {
            "name": "Medium Sorted Array",
            "size_category": "medium",
            "data": list(range(1000)),
            "difficulty": "best_case"
        },
        {
            "name": "Medium Reverse Array",
            "size_category": "medium", 
            "data": list(range(1000, 0, -1)),
            "difficulty": "worst_case"
        },
        {
            "name": "Single Element",
            "size_category": "small",
            "data": [42],
            "difficulty": "best_case"
        },
        {
            "name": "Empty Array",
            "size_category": "small",
            "data": [],
            "difficulty": "best_case"
        },
        {
            "name": "Two Elements Sorted",
            "size_category": "small",
            "data": [1, 2],
            "difficulty": "best_case"
        },
        {
            "name": "Two Elements Reverse",
            "size_category": "small", 
            "data": [2, 1],
            "difficulty": "worst_case"
        },
        {
            "name": "Duplicates Array",
            "size_category": "small",
            "data": [5, 2, 8, 2, 9, 1, 5, 5, 3, 7, 2, 8, 1, 9, 5],
            "difficulty": "random"
        }
    ]
    
    for case_data in sample_cases:
        expected = sorted(case_data["data"])
        test_case = TestCase(
            name=case_data["name"],
            size_category=case_data["size_category"],
            data=case_data["data"],
            expected_result=expected,
            difficulty=case_data["difficulty"]
        )
        db.add(test_case)
    
    db.commit()
    print(f"Created {len(sample_cases)} sample test cases")
