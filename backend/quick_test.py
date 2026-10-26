"""
Quick integration test for Class 12 redesign.
Tests basic functionality without full test suite.
"""
import json
from models.student_model import StudentModel
from services.counsellor_prompts import (
    SYSTEM_PROMPT,
    build_extraction_prompt,
    get_branch_description
)
from engines.adaptive_engine_llm import LLMAdaptiveEngine
import services.llm_client as llm_client


def test_student_model():
    """Test StudentModel basic operations."""
    print("\n=== Testing StudentModel ===")
    
    model = StudentModel()
    print(f"Initial state: {model.branch_hypothesis}, confidence: {model.hypothesis_confidence}")
    
    # Apply updates
    trait_updates = {
        "hands_on": 0.8,
        "spatial_reasoning": 0.7,
        "math_aptitude": 0.65
    }
    profile_updates = {
        "interests": ["fixing bicycles", "building things"],
        "motivations": ["helping people"]
    }
    
    model.apply_updates(trait_updates, profile_updates)
    print(f"After updates: hands_on={model.hands_on:.2f}, interests={model.interests}")
    
    # Calculate branch scores
    scores = model.calculate_branch_scores()
    print(f"Branch scores: {scores}")
    
    top_branches = model.get_top_branches(3)
    print(f"Top 3 branches: {[b['branch'] for b in top_branches]}")
    
    # Convert to dict
    model_dict = model.to_dict()
    print(f"Serialized keys: {list(model_dict.keys())}")
    
    print("✅ StudentModel test passed\n")


def test_prompts():
    """Test prompt generation."""
    print("\n=== Testing Prompts ===")
    
    model = StudentModel()
    model.interests = ["physics", "machines"]
    
    prompt = build_extraction_prompt(
        student_answer="I love taking apart old radios",
        question_asked="What do you like to do on weekends?",
        student_model=model.to_dict(),
        questions_asked_so_far=["What is your favorite subject?"],
        current_stage="interest_probes",
        turn_number=4
    )
    
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Contains 'trait_updates': {'trait_updates' in prompt}")
    print(f"Contains 'next_question': {'next_question' in prompt}")
    
    # Test branch description
    desc = get_branch_description("Mech")
    print(f"Mech description: {desc}")
    
    print("✅ Prompts test passed\n")


def test_engine_initialization():
    """Test LLM engine initialization."""
    print("\n=== Testing Engine Initialization ===")
    
    engine = LLMAdaptiveEngine()
    print(f"Loaded {len(engine.opener_questions)} opener questions")
    print(f"Loaded {len(engine.stage_templates)} stage templates")
    print(f"Loaded {len(engine.branch_profiles)} branch profiles")
    
    # Test session creation
    session = engine.create_session(
        exam_type="jee_main",
        rank=5000,
        max_questions=8
    )
    
    print(f"Session created: {list(session.keys())}")
    print(f"Student model type: {type(session['student_model'])}")
    
    # Test opening question
    opening = engine.select_opening_question(session)
    print(f"Opening question: {opening['text'][:50]}...")
    
    print("✅ Engine initialization test passed\n")


def test_llm_availability():
    """Test LLM client availability."""
    print("\n=== Testing LLM Availability ===")
    
    health = llm_client.check_llm_health()
    print(f"Active provider: {health.get('active_provider', 'none')}")
    print(f"Active model: {health.get('active_model', 'none')}")
    print(f"Groq available: {health.get('groq', False)}")
    print(f"Ollama available: {health.get('ollama', False)}")
    
    if health.get('active_provider'):
        print("✅ LLM is available")
    else:
        print("❌ No LLM available")
    
    print()


def test_single_turn():
    """Test processing a single answer."""
    print("\n=== Testing Single Turn Processing ===")
    
    engine = LLMAdaptiveEngine()
    session = engine.create_session()
    
    # Get first question
    q1 = engine.select_opening_question(session)
    print(f"Q1: {q1['text']}")
    
    # Process first answer
    answer1 = "I'd probably spend it fixing my bicycle or taking apart old electronics."
    print(f"A1: {answer1}")
    
    try:
        result = engine.process_answer(session, answer1, llm_client)
        
        print(f"\nResult keys: {list(result.keys())}")
        print(f"Is complete: {result['is_complete']}")
        print(f"Confidence: {result['confidence']:.2%}")
        
        if result.get('question'):
            print(f"Next question: {result['question']['text'][:80]}...")
        
        model = result['student_model']
        print(f"Student model - hands_on: {model.hands_on:.2f}")
        print(f"Student model - interests: {model.interests}")
        
        print("✅ Single turn test passed")
        
    except Exception as e:
        print(f"❌ Single turn test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def main():
    """Run all quick tests."""
    print("\n" + "="*80)
    print("  PATHFINDER CLASS 12 REDESIGN - QUICK TEST")
    print("="*80)
    
    try:
        test_student_model()
        test_prompts()
        test_engine_initialization()
        test_llm_availability()
        
        # Only run single turn if LLM available
        health = llm_client.check_llm_health()
        if health.get('active_provider'):
            test_single_turn()
        else:
            print("⚠️  Skipping single turn test (no LLM available)\n")
        
        print("="*80)
        print("  ALL QUICK TESTS COMPLETED")
        print("="*80)
        print()
        
    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
