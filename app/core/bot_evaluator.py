import signal
import subprocess
import tempfile
import json
import time
import os
import asyncio
import logging

from typing import List, Optional, Dict, Any
from app.models.db_models import Bot, TestCase, BotSubmission, BotResult
from sqlalchemy.orm import Session

# Bot Evaluation Service
class BotEvaluator:
    def __init__(self):
        self.timeout_seconds = 30  # 30 second timeout per test case
    
    async def evaluate_bot(self, bot_code: str, test_cases: List[TestCase], submission_id: str, db: Session):
        """Evaluate a bot against all test cases"""
        results = []
        
        for test_case in test_cases:
            try:
                result = await self._run_single_test(bot_code, test_case, submission_id, db)
                results.append(result)
            except Exception as e:
                logging.error(f"Error evaluating test case {test_case.id}: {str(e)}")
                # Create failed result
                result = BotResult(
                    submission_id=submission_id,
                    test_case_id=test_case.id,
                    success="error",
                    error_message=str(e)
                )
                db.add(result)
                results.append(result)
        
        # Calculate total score (average execution time, lower is better)
        successful_results = [r for r in results if r.success == "pass" and r.execution_time is not None]
        if successful_results:
            total_score = sum(r.execution_time for r in successful_results) / len(successful_results)
        else:
            total_score = 0  # Penalty for failed bots
        
        # Update submission with total score
        submission = db.query(BotSubmission).filter(BotSubmission.id == submission_id).first()
        submission.total_score = total_score
        submission.status = "completed"
        
        db.commit()
        return results
    
    async def _run_single_test(self, bot_code: str, test_case: TestCase, submission_id: str, db: Session) -> BotResult:
        """Run bot against a single test case with timeout protection"""
        
        # Create a temporary file with the bot code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Wrap the bot code to make it executable
            wrapped_code = f"""
import json
import sys
import time

# Bot code starts here
{bot_code}

# Test execution
if __name__ == "__main__":
    test_data = {json.dumps(test_case.data)}
    start_time = time.time()
    
    try:
        # Assume the bot defines a function called 'sort_array'
        if 'sort_array' in globals():
            result = sort_array(test_data.copy())
        else:
            # Fallback: try to find any function that takes a list
            import inspect
            functions = [obj for name, obj in globals().items() 
                        if inspect.isfunction(obj) and not name.startswith('_')]
            if functions:
                result = functions[0](test_data.copy())
            else:
                raise Exception("No sorting function found")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify result
        expected = {json.dumps(test_case.expected_result)}
        if result == expected:
            print(f"PASS,{{execution_time}}")
        else:
            print(f"FAIL,{{execution_time}},Result mismatch")
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"ERROR,{{execution_time}},{{str(e)}}")
"""
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Run the bot with timeout
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout_seconds
                )
                execution_time = time.time() - start_time
                
                # Parse result
                output = stdout.decode().strip()
                if output.startswith("PASS"):
                    parts = output.split(',')
                    actual_time = float(parts[1]) if len(parts) > 1 else execution_time
                    result = BotResult(
                        submission_id=submission_id,
                        test_case_id=test_case.id,
                        execution_time=actual_time,
                        success="pass"
                    )
                elif output.startswith("FAIL"):
                    parts = output.split(',', 2)
                    actual_time = float(parts[1]) if len(parts) > 1 else execution_time
                    error_msg = parts[2] if len(parts) > 2 else "Test failed"
                    result = BotResult(
                        submission_id=submission_id,
                        test_case_id=test_case.id,
                        execution_time=actual_time,
                        success="fail",
                        error_message=error_msg
                    )
                else:
                    # Error case
                    parts = output.split(',', 2)
                    actual_time = float(parts[1]) if len(parts) > 1 else execution_time
                    error_msg = parts[2] if len(parts) > 2 else stderr.decode()
                    result = BotResult(
                        submission_id=submission_id,
                        test_case_id=test_case.id,
                        execution_time=actual_time,
                        success="error",
                        error_message=error_msg
                    )
                
            except asyncio.TimeoutError:
                process.kill()
                result = BotResult(
                    submission_id=submission_id,
                    test_case_id=test_case.id,
                    execution_time=self.timeout_seconds,
                    success="timeout",
                    error_message="Execution timed out"
                )
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
        
        db.add(result)
        return result
