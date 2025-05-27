"""
Script to load test cases from the provided input files into the database
"""

import os
import sys
from sqlalchemy.orm import Session
from app.main import SessionLocal
from app.models.db_models import TestCase

def parse_input_file(filename):
    """Parse a comma-separated input file into arrays"""
    arrays = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Parse comma-separated integers
                    array = [int(x) for x in line.split(',')]
                    arrays.append(array)
    except FileNotFoundError:
        print(f"Warning: {filename} not found, skipping...")
        return []
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return []
    
    return arrays

def load_test_cases(filename, size='small'):
    """Load test cases from input files into database"""
    db = SessionLocal()
    
    try:
        print("Loading test cases from input files...")
        
        # Load test cases
        arrays = parse_input_file(filename)
        print(f"Loaded {len(arrays)} small test cases")
        
        
        # Create test cases for arrays
        for i, array in enumerate(arrays):
            expected = sorted(array)
            
            # Determine difficulty based on the array characteristics
            if array == expected:
                difficulty = "best_case"
            elif array == sorted(array, reverse=True):
                difficulty = "worst_case"
            elif i == 0:  # First array is typically sorted
                difficulty = "best_case"
            elif i == 1:  # Second array is typically reverse sorted
                difficulty = "worst_case"
            else:
                difficulty = "random"
            
            test_case = TestCase(
                name=f"Test Case {i+1}",
                size_category=size,
                data=array,
                expected_result=expected,
                difficulty=difficulty
            )
            db.add(test_case)
        
        
        # Commit all test cases
        db.commit()
        total_cases = len(arrays)
        print(f"Successfully loaded {total_cases} test cases into database")
        
    except Exception as e:
        print(f"Error loading test cases: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_test_cases():
    """Create a few sample test cases for development/testing"""
    db = SessionLocal()
    
    try:
        # Check if test cases already exist
        existing_count = db.query(TestCase).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing test cases. Skipping sample data creation.")
            return
        
        print("Creating sample test cases...")
        
        # Sample test cases
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
                "data": [64, 34, 25, 12, 22, 11, 90, 5, 77, 30],
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
                "data": [5, 2, 8, 2, 9, 1, 5, 5],
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
        
    except Exception as e:
        print(f"Error creating sample test cases: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Sort Bot Test Data Loader")
    print("=" * 40)
    
    # Try to load from actual input files first
    filename = './data/inputs_small.txt'
    if os.path.exists(filename):
        load_test_cases(filename, size='small')
    else:
        print("Input files not found, creating sample test cases instead...")
        create_sample_test_cases()
    
    print("Test data loading complete!")