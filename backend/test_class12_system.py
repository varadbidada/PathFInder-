"""
Test script for the redesigned Class 12 student question system.
Tests the full pipeline with realistic student answers.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
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


def print_model_state(model: StudentModel, turn: int):
    """Print current state of student model."""
    print(f"\n📊 Student Model After Turn {turn}:")
    print_separator()
    
    # Traits
    print("Traits:")
    traits = {
        "Math Aptitude": model.math_aptitude,
        "Logical Thinking": model.logical_thinking,
        "Creativity": model.creativity,
        "Hands-On": model.hands_on,
        "Spatial Reasoning": model.spatial_reasoning,
        "Biology Interest": model.biology_interest,
        "Problem Solving": model.problem_solving,
    }
    for trait, value in traits.items():
        bar = "█" * int(value * 20)
        print(f"  {trait:20s} [{value:.2f}] {bar}")
    
    # Categorical
    print(f"\n  Risk Appetite: {model.risk_appetite}")
    print(f"  Work Style: {model.work_style}")
    print(f"  Memory Preference: {model.memory_preference}")
    
    # Qualitative
    if model.interests:
        print(f"\n  Interests: {', '.join(model.interests)}")
    if model.aversions:
        print(f"  Aversions: {', '.join(model.aversions)}")
    if model.motivations:
        print(f"  Motivations: {', '.join(model.motivations)}")
    if model.notable_quotes:
        print(f"  Notable Quotes: {model.notable_quotes}")
    
    # Hypothesis
    print(f"\n  Branch Hypothesis: {model.branch_hypothesis}")
    print(f"  Confidence: {model.hypothesis_confidence:.2%}")
    
    # Branch scores
    print(f"\n  Branch Scores:")
    scores = model.calculate_branch_scores()
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for branch, score in sorted_scores:
        bar = "█" * int(score * 20)
        print(f"    {branch:10s} [{score:.2f}] {bar}")
    
    print_separator()


async def test_mechanical_student():
    """
    Test the system with a student who should match Mechanical Engineering.
    
    Expected outcome:
    - Branch hypothesis: Mech or ECE
    - High hands_on score
    - High spatial_reasoning score
    - Interests should include physical objects, machines
    """
    print_section("TEST: Mechanical Engineering Student")
    
    # Initialize engine
    engine = LLMAdaptiveEngine()
    
    # Create session
    session = engine.create_session(
        exam_type="jee_main",
        rank=5000,
        max_questions=8
    )
    
    print("✅ Session created")
    print(f"Engine: LLM-powered")
    print(f"Max questions: {session['max_questions']}")
    print()
    
    # Test answers sequence
    test_answers = [
        # Turn 1: Q1 opener - Saturday activity
        "I'd probably spend it taking apart my old radio or fixing my bicycle.",
        
        # Turn 2: Q2 opener - Subject
        "Physics was the best — especially when we derived things from scratch.",
        
        # Turn 3: Q3 opener - 10 years from now
        "I want to build machines that actually help people.",
        
        # Turn 4+: LLM-generated questions
        "I love understanding how things work mechanically. Like, when something breaks, "
        "I want to open it up and see the parts inside.",
        
        "I prefer hands-on experiments over just reading theory. Building something "
        "physical is way more satisfying.",
        
        "I think I'd be good at designing physical systems, like robots or engines. "
        "I like the idea of creating something you can actually touch.",
    ]
    
    # Process each answer
    for turn, answer in enumerate(test_answers, start=1):
        print(f"\n{'='*80}")
        print(f"Turn {turn}")
        print(f"{'='*80}")
        
        if turn == 1:
            # First question is the opener
            question = engine.select_opening_question(session)
            print(f"\n🤖 Pathfinder: {question['text']}")
        
        print(f"\n👤 Student: {answer}")
        
        # Process answer
        try:
            result = engine.process_answer(session, answer, llm_client)
            
            # Print next question if not complete
            if not result["is_complete"] and result.get("question"):
                next_q = result["question"]
                print(f"\n🤖 Pathfinder: {next_q['text']}")
                if next_q.get('reasoning'):
                    print(f"   💡 Reasoning: {next_q['reasoning']}")
            
            # Print model state
            print_model_state(result["student_model"], turn)
            
            # Check completion
            if result["is_complete"]:
                print("\n" + "="*80)
                print("  SESSION COMPLETE")
                print("="*80)
                break
                
        except Exception as e:
            print(f"\n❌ Error processing turn {turn}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Final validation
    print_section("TEST VALIDATION")
    
    final_model = session["student_model"]
    final_scores = final_model.calculate_branch_scores()
    top_branch = max(final_scores.items(), key=lambda x: x[1])
    
    print(f"Final Branch Hypothesis: {final_model.branch_hypothesis}")
    print(f"Final Confidence: {final_model.hypothesis_confidence:.2%}")
    print(f"Top Branch by Score: {top_branch[0]} ({top_branch[1]:.2f})")
    print()
    
    # Validation checks
    checks = []
    
    # Check 1: Branch should be Mech or ECE
    if final_model.branch_hypothesis in ["Mech", "ECE"]:
        checks.append("✅ Branch hypothesis is Mech or ECE (expected)")
    else:
        checks.append(f"❌ Branch hypothesis is {final_model.branch_hypothesis} (expected Mech/ECE)")
    
    # Check 2: Confidence should be > 0.4
    if final_model.hypothesis_confidence > 0.4:
        checks.append(f"✅ Confidence > 0.4 ({final_model.hypothesis_confidence:.2%})")
    else:
        checks.append(f"❌ Confidence too low ({final_model.hypothesis_confidence:.2%})")
    
    # Check 3: Hands-on score should be high
    if final_model.hands_on > 0.6:
        checks.append(f"✅ High hands-on score ({final_model.hands_on:.2f})")
    else:
        checks.append(f"❌ Low hands-on score ({final_model.hands_on:.2f})")
    
    # Check 4: Should have interests related to machines/physical
    physical_keywords = ["machine", "physical", "mechanical", "build", "fix", "parts", "robot"]
    has_physical_interest = any(
        any(kw in interest.lower() for kw in physical_keywords)
        for interest in final_model.interests
    )
    if has_physical_interest:
        checks.append("✅ Interests include physical/mechanical topics")
    else:
        checks.append(f"❌ No physical interests found: {final_model.interests}")
    
    # Check 5: No question should have been repeated
    questions_asked = session["questions_asked"]
    unique_questions = len(set(questions_asked))
    if unique_questions == len(questions_asked):
        checks.append(f"✅ No duplicate questions ({len(questions_asked)} unique)")
    else:
        checks.append(f"❌ {len(questions_asked) - unique_questions} duplicate questions")
    
    # Print results
    print("Validation Results:")
    for check in checks:
        print(f"  {check}")
    
    print()
    passed = all("✅" in check for check in checks)
    if passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    
    return passed


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  PATHFINDER CLASS 12 QUESTION SYSTEM TEST SUITE")
    print("="*80)
    print()
    
    # Check LLM availability
    print("Checking LLM availability...")
    health = llm_client.check_llm_health()
    print(f"  Provider: {health.get('active_provider', 'none')}")
    print(f"  Model: {health.get('active_model', 'none')}")
    print()
    
    if not health.get("active_provider"):
        print("❌ No LLM available. Please set GROQ_API_KEY or install Ollama.")
        return False
    
    # Run tests
    try:
        result = await test_mechanical_student()
        return result
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
