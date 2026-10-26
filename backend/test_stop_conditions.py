"""
Quick test to verify the stop condition logic is correct.
Tests the _should_stop() method without needing actual LLM calls.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engines.adaptive_engine_llm import LLMAdaptiveEngine
from models.student_model import StudentModel


def test_stop_conditions():
    """Test that _should_stop() enforces all conditions correctly."""
    print("\n" + "="*80)
    print("  TESTING STOP CONDITIONS")
    print("="*80)
    print()
    
    engine = LLMAdaptiveEngine()
    
    # Test 1: Should NOT stop before turn 8
    print("Test 1: Should NOT stop before turn 8")
    model = StudentModel()
    # Even with all traits measured and high confidence
    model.math_aptitude = 0.8
    model.logical_thinking = 0.8
    model.creativity = 0.7
    model.hands_on = 0.6
    model.spatial_reasoning = 0.7
    model.biology_interest = 0.3
    model.problem_solving = 0.8
    model.risk_appetite = "medium"
    model.work_style = "team"
    model.memory_preference = "conceptual"
    model.hypothesis_confidence = 0.90
    
    should_stop = engine._should_stop(model, turn=7, questions_asked=[])
    print(f"  Turn 7 with all traits + high confidence: {should_stop}")
    assert should_stop == False, "❌ FAILED: Should not stop before turn 8"
    print("  ✅ PASSED: Did not stop before turn 8\n")
    
    # Test 2: Should NOT stop if numeric trait still at default
    print("Test 2: Should NOT stop if numeric trait still at default")
    model2 = StudentModel()
    model2.math_aptitude = 0.8
    model2.logical_thinking = 0.8
    model2.creativity = 0.7
    model2.hands_on = 0.6
    model2.spatial_reasoning = 0.7
    model2.biology_interest = 0.3
    model2.problem_solving = 0.5  # Still at default!
    model2.risk_appetite = "medium"
    model2.work_style = "team"
    model2.memory_preference = "conceptual"
    model2.hypothesis_confidence = 0.90
    
    should_stop = engine._should_stop(model2, turn=10, questions_asked=[])
    print(f"  Turn 10, problem_solving still 0.5: {should_stop}")
    assert should_stop == False, "❌ FAILED: Should not stop with unmeasured trait"
    print("  ✅ PASSED: Did not stop with unmeasured trait\n")
    
    # Test 3: Should NOT stop if categorical trait is None
    print("Test 3: Should NOT stop if categorical trait is None")
    model3 = StudentModel()
    model3.math_aptitude = 0.8
    model3.logical_thinking = 0.8
    model3.creativity = 0.7
    model3.hands_on = 0.6
    model3.spatial_reasoning = 0.7
    model3.biology_interest = 0.3
    model3.problem_solving = 0.7
    model3.risk_appetite = "medium"
    model3.work_style = "team"
    model3.memory_preference = None  # Never observed!
    model3.hypothesis_confidence = 0.90
    
    should_stop = engine._should_stop(model3, turn=10, questions_asked=[])
    print(f"  Turn 10, memory_preference None: {should_stop}")
    assert should_stop == False, "❌ FAILED: Should not stop with unobserved categorical"
    print("  ✅ PASSED: Did not stop with unobserved categorical\n")
    
    # Test 4: Should NOT stop if confidence < 0.85
    print("Test 4: Should NOT stop if confidence < 0.85")
    model4 = StudentModel()
    model4.math_aptitude = 0.8
    model4.logical_thinking = 0.8
    model4.creativity = 0.7
    model4.hands_on = 0.6
    model4.spatial_reasoning = 0.7
    model4.biology_interest = 0.3
    model4.problem_solving = 0.7
    model4.risk_appetite = "medium"
    model4.work_style = "team"
    model4.memory_preference = "conceptual"
    model4.hypothesis_confidence = 0.80  # Below threshold!
    
    should_stop = engine._should_stop(model4, turn=10, questions_asked=[])
    print(f"  Turn 10, confidence 0.80 < 0.85: {should_stop}")
    assert should_stop == False, "❌ FAILED: Should not stop with low confidence"
    print("  ✅ PASSED: Did not stop with low confidence\n")
    
    # Test 5: SHOULD stop when all conditions met
    print("Test 5: SHOULD stop when all conditions met")
    model5 = StudentModel()
    model5.math_aptitude = 0.8
    model5.logical_thinking = 0.8
    model5.creativity = 0.7
    model5.hands_on = 0.6
    model5.spatial_reasoning = 0.7
    model5.biology_interest = 0.3
    model5.problem_solving = 0.7
    model5.risk_appetite = "medium"
    model5.work_style = "team"
    model5.memory_preference = "conceptual"
    model5.hypothesis_confidence = 0.87
    
    should_stop = engine._should_stop(model5, turn=10, questions_asked=[])
    print(f"  Turn 10, all traits measured, confidence 0.87: {should_stop}")
    assert should_stop == True, "❌ FAILED: Should stop when all conditions met"
    print("  ✅ PASSED: Stopped when all conditions met\n")
    
    # Test 6: MUST stop at hard cap (15 questions)
    print("Test 6: MUST stop at hard cap (15 questions)")
    model6 = StudentModel()  # Even with nothing measured
    
    should_stop = engine._should_stop(model6, turn=15, questions_asked=[])
    print(f"  Turn 15 (hard cap), nothing measured: {should_stop}")
    assert should_stop == True, "❌ FAILED: Must stop at hard cap"
    print("  ✅ PASSED: Stopped at hard cap\n")
    
    # Test 7: Test get_most_uncertain_trait priority
    print("Test 7: Test get_most_uncertain_trait priority")
    
    # Categorical None should be highest priority
    model7 = StudentModel()
    model7.math_aptitude = 0.8
    model7.logical_thinking = 0.8
    model7.risk_appetite = None  # Categorical missing
    
    trait = engine._get_most_uncertain_trait(model7)
    print(f"  Categorical None: {trait}")
    assert trait == "risk_appetite", "❌ FAILED: Should prioritize categorical None"
    print("  ✅ PASSED: Prioritized categorical None\n")
    
    # Numeric default should be second priority
    model8 = StudentModel()
    model8.risk_appetite = "medium"
    model8.work_style = "team"
    model8.memory_preference = "conceptual"
    model8.math_aptitude = 0.5  # Still at default
    model8.logical_thinking = 0.7
    
    trait = engine._get_most_uncertain_trait(model8)
    print(f"  Numeric at default: {trait}")
    assert trait == "math_aptitude", "❌ FAILED: Should prioritize numeric default"
    print("  ✅ PASSED: Prioritized numeric default\n")
    
    # Test 8: Test get_uncovered_traits
    print("Test 8: Test get_uncovered_traits")
    model9 = StudentModel()
    model9.math_aptitude = 0.8
    model9.logical_thinking = 0.7
    model9.creativity = 0.6
    model9.hands_on = 0.8
    model9.spatial_reasoning = 0.5  # Default
    model9.biology_interest = 0.3
    model9.problem_solving = 0.5  # Default
    model9.risk_appetite = None  # Missing
    model9.work_style = "team"
    model9.memory_preference = None  # Missing
    
    uncovered = engine.get_uncovered_traits(model9)
    print(f"  Uncovered: {uncovered}")
    assert len(uncovered['numeric']) == 2, f"❌ FAILED: Should have 2 numeric, got {len(uncovered['numeric'])}"
    assert len(uncovered['categorical']) == 2, f"❌ FAILED: Should have 2 categorical, got {len(uncovered['categorical'])}"
    assert uncovered['total_uncovered'] == 4, f"❌ FAILED: Should have 4 total, got {uncovered['total_uncovered']}"
    print("  ✅ PASSED: Correctly identified uncovered traits\n")
    
    return True


def main():
    """Run all stop condition tests."""
    print("\n" + "="*80)
    print("  PATHFINDER STOP CONDITION TESTS")
    print("  Verifying trait coverage enforcement logic")
    print("="*80)
    
    try:
        success = test_stop_conditions()
        
        print("="*80)
        if success:
            print("  🎉 ALL TESTS PASSED")
        else:
            print("  ❌ SOME TESTS FAILED")
        print("="*80)
        print()
        
        return success
        
    except AssertionError as e:
        print(f"\n{e}")
        print("\n" + "="*80)
        print("  ❌ TEST FAILED")
        print("="*80)
        print()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
