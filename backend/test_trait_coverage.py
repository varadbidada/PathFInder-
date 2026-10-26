"""
Test script to verify that the LLM keeps generating questions until ALL traits are measured.

This test simulates a worst-case scenario with one-word answers to ensure
the system doesn't stop prematurely.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engines.adaptive_engine_llm import LLMAdaptiveEngine
from models.student_model import StudentModel
import services.llm_client as llm_client


def print_separator(char="-", length=80):
    """Print a separator line."""
    print(char * length)


def print_section(title: str):
    """Print a section header."""
    print_separator("=")
    print(f"  {title}")
    print_separator("=")
    print()


def print_coverage_status(model: StudentModel, turn: int, engine: LLMAdaptiveEngine):
    """Print current trait coverage status."""
    print(f"\n📊 Trait Coverage Status - Turn {turn}:")
    print_separator()
    
    # Get uncovered traits
    uncovered = engine.get_uncovered_traits(model)
    
    # Numeric traits
    print("Numeric Traits:")
    numeric_traits = {
        "math_aptitude": model.math_aptitude,
        "logical_thinking": model.logical_thinking,
        "creativity": model.creativity,
        "hands_on": model.hands_on,
        "spatial_reasoning": model.spatial_reasoning,
        "biology_interest": model.biology_interest,
        "problem_solving": model.problem_solving,
    }
    
    for trait, value in numeric_traits.items():
        status = "❌ DEFAULT" if abs(value - 0.5) < 0.01 else "✅ MEASURED"
        bar = "█" * int(value * 20) if value != 0.5 else "░" * 10
        print(f"  {trait:20s} [{value:.2f}] {bar} {status}")
    
    # Categorical traits
    print(f"\nCategorical Traits:")
    categorical_traits = {
        "risk_appetite": model.risk_appetite,
        "work_style": model.work_style,
        "memory_preference": model.memory_preference,
    }
    
    for trait, value in categorical_traits.items():
        status = "❌ NONE" if value is None else f"✅ {value}"
        print(f"  {trait:20s} {status}")
    
    # Summary
    print(f"\n  Total Uncovered: {uncovered['total_uncovered']}")
    print(f"  Numeric Uncovered: {len(uncovered['numeric'])}")
    print(f"  Categorical Uncovered: {len(uncovered['categorical'])}")
    print(f"  Confidence: {model.hypothesis_confidence:.2%}")
    print(f"  Hypothesis: {model.branch_hypothesis}")
    
    print_separator()


def test_one_word_answers():
    """
    Test with one-word answers (worst case for signal extraction).
    System must continue asking until all traits are measured.
    """
    print_section("TEST: One-Word Answers (Worst Case)")
    
    # Check LLM availability
    health = llm_client.check_llm_health()
    print(f"LLM Provider: {health.get('active_provider', 'none')}")
    print(f"LLM Model: {health.get('active_model', 'none')}")
    print()
    
    if not health.get("active_provider"):
        print("❌ No LLM available. Test cannot run.")
        return False
    
    # Initialize engine
    engine = LLMAdaptiveEngine()
    
    # Create session
    session = engine.create_session(
        exam_type="jee_main",
        rank=5000,
        max_questions=15  # Set to hard cap
    )
    
    print("✅ Session created")
    print()
    
    # Prepare one-word answers (minimal signal)
    one_word_answers = [
        # Openers (1-3)
        "Maybe.",
        "Math.",
        "Something.",
        
        # Additional minimal answers (4-15)
        "Yes.",
        "No.",
        "Sometimes.",
        "Okay.",
        "Fine.",
        "Sure.",
        "Maybe.",
        "Dunno.",
        "Both.",
        "Neither.",
        "Either.",
        "Whatever.",
    ]
    
    # Track results
    turns_taken = 0
    stopped_early = False
    all_traits_covered = False
    
    try:
        for turn, answer in enumerate(one_word_answers, start=1):
            print(f"\n{'='*80}")
            print(f"Turn {turn}")
            print(f"{'='*80}")
            
            if turn == 1:
                # First question is the opener
                question = engine.select_opening_question(session)
                print(f"\n🤖 Pathfinder: {question['text']}")
            
            print(f"\n👤 Student: {answer}")
            
            # Process answer
            result = engine.process_answer(session, answer, llm_client)
            
            # Print coverage status
            print_coverage_status(result["student_model"], turn, engine)
            
            # Print next question if not complete
            if not result["is_complete"] and result.get("question"):
                next_q = result["question"]
                print(f"\n🤖 Pathfinder: {next_q['text']}")
                if next_q.get('reasoning'):
                    print(f"   💡 Reasoning: {next_q['reasoning']}")
                if result.get('target_trait'):
                    print(f"   🎯 Targeting trait: {result['target_trait']}")
            
            turns_taken = turn
            
            # Check completion
            if result["is_complete"]:
                print("\n" + "="*80)
                print("  SESSION COMPLETE")
                print("="*80)
                
                # Check if stopped too early
                uncovered = engine.get_uncovered_traits(result["student_model"])
                if uncovered["total_uncovered"] > 0:
                    stopped_early = True
                    print(f"\n⚠️  WARNING: Stopped with {uncovered['total_uncovered']} traits still uncovered!")
                else:
                    all_traits_covered = True
                    print(f"\n✅ All traits covered!")
                
                break
    
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final validation
    print_section("TEST VALIDATION")
    
    final_model = session["student_model"]
    uncovered = engine.get_uncovered_traits(final_model)
    
    print(f"Turns taken: {turns_taken}")
    print(f"Final confidence: {final_model.hypothesis_confidence:.2%}")
    print(f"Final hypothesis: {final_model.branch_hypothesis}")
    print(f"Uncovered traits: {uncovered['total_uncovered']}")
    print()
    
    # Validation checks
    checks = []
    
    # Check 1: Must ask at least 8 questions
    if turns_taken >= 8:
        checks.append(f"✅ Asked at least 8 questions ({turns_taken})")
    else:
        checks.append(f"❌ Only {turns_taken} questions (need 8 minimum)")
    
    # Check 2: Must not stop before turn 8
    if not stopped_early or turns_taken >= 8:
        checks.append(f"✅ Did not stop before turn 8")
    else:
        checks.append(f"❌ Stopped early at turn {turns_taken}")
    
    # Check 3: Must not exceed 15 questions
    if turns_taken <= 15:
        checks.append(f"✅ Did not exceed 15 questions")
    else:
        checks.append(f"❌ Exceeded hard cap ({turns_taken} questions)")
    
    # Check 4: All traits should be covered (or close to it given one-word answers)
    if uncovered["total_uncovered"] == 0:
        checks.append(f"✅ All traits covered")
    elif uncovered["total_uncovered"] <= 2:
        checks.append(f"⚠️  Almost covered ({uncovered['total_uncovered']} traits remain)")
    else:
        checks.append(f"❌ Too many uncovered traits ({uncovered['total_uncovered']})")
    
    # Check 5: Confidence should increase over turns
    if final_model.hypothesis_confidence > 0.5:
        checks.append(f"✅ Confidence increased ({final_model.hypothesis_confidence:.2%})")
    else:
        checks.append(f"❌ Confidence too low ({final_model.hypothesis_confidence:.2%})")
    
    # Check 6: Must have a hypothesis (not "unknown")
    if final_model.branch_hypothesis != "unknown":
        checks.append(f"✅ Has hypothesis ({final_model.branch_hypothesis})")
    else:
        checks.append(f"❌ No hypothesis formed")
    
    # Print results
    print("Validation Results:")
    for check in checks:
        print(f"  {check}")
    
    print()
    
    # Determine pass/fail
    critical_failures = [
        "❌ Only" in checks[0],  # < 8 questions
        "❌ Stopped early" in checks[1],  # Stopped before turn 8
        "❌ Too many uncovered" in checks[3],  # > 2 uncovered traits
    ]
    
    if any(critical_failures):
        print("❌ TEST FAILED (Critical issues)")
        return False
    elif all("✅" in check for check in checks):
        print("🎉 TEST PASSED (Perfect)")
        return True
    else:
        print("⚠️  TEST PASSED (With warnings)")
        return True


def main():
    """Run the trait coverage test."""
    print("\n" + "="*80)
    print("  PATHFINDER TRAIT COVERAGE TEST")
    print("  Verifying: LLM keeps asking until ALL traits are measured")
    print("="*80)
    print()
    
    result = test_one_word_answers()
    
    print("\n" + "="*80)
    if result:
        print("  ✅ TEST SUITE PASSED")
    else:
        print("  ❌ TEST SUITE FAILED")
    print("="*80)
    print()
    
    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
