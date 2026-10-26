"""
Debug script to test LLM response for a specific question/answer pair.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.student_model import StudentModel
from services.counsellor_prompts import build_extraction_prompt, SYSTEM_PROMPT
from services.llm_client import call_llm
import json


def test_specific_answer():
    """Test the specific answer that's failing."""
    print("\n" + "="*80)
    print("  LLM RESPONSE DEBUG")
    print("="*80)
    print()
    
    # Create a basic student model
    model = StudentModel()
    
    # Simulate the question/answer pair that's failing
    question = "Would you take a chance on a new career if it meant starting from scratch, but with the potential for something amazing?"
    answer = "yes would love that"
    
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print()
    
    # Build the extraction prompt
    prompt = build_extraction_prompt(
        student_answer=answer,
        question_asked=question,
        student_model=model.to_dict(),
        questions_asked_so_far=[],
        current_stage="personality",
        turn_number=1,
        target_trait="risk_appetite"
    )
    
    print("Prompt length:", len(prompt), "characters")
    print()
    print("Calling LLM...")
    print()
    
    try:
        # Call LLM
        response = call_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            expect_json=True,
            temperature=0.7,
            max_tokens=1200
        )
        
        print("="*80)
        print("LLM RESPONSE:")
        print("="*80)
        
        if isinstance(response, dict):
            print(json.dumps(response, indent=2))
            print()
            print("✅ SUCCESS: Response is valid JSON")
            
            # Check required fields
            required_fields = ["trait_updates", "profile_updates", "branch_hypothesis", 
                             "hypothesis_confidence", "next_question", "next_question_reasoning"]
            
            missing = [f for f in required_fields if f not in response]
            if missing:
                print(f"⚠️ WARNING: Missing fields: {missing}")
            else:
                print("✅ All required fields present")
                
        else:
            print(response)
            print()
            print("❌ ERROR: Response is not a dict, likely string")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_simple_call():
    """Test a simple LLM call to verify it's working."""
    print("\n" + "="*80)
    print("  SIMPLE LLM TEST")
    print("="*80)
    print()
    
    try:
        response = call_llm(
            prompt="Return this JSON: {\"status\": \"ok\", \"message\": \"Hello\"}",
            system_prompt="You are a helpful assistant. Return ONLY valid JSON.",
            expect_json=True,
            max_tokens=100
        )
        
        print("Response:", response)
        
        if isinstance(response, dict) and response.get("status") == "ok":
            print("✅ Simple test passed")
        else:
            print("⚠️ Simple test returned unexpected format")
            
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
    
    print()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  DEBUGGING LLM RESPONSE ISSUE")
    print("="*80)
    
    # First test simple call
    test_simple_call()
    
    # Then test the specific failing case
    test_specific_answer()
    
    print("="*80)
    print("  DEBUG COMPLETE")
    print("="*80)
    print()
