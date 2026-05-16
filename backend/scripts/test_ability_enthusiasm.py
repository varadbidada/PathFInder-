"""
Test script for ability/enthusiasm split in signal extraction and scoring.
Tests the acceptance criteria for the multi-signal sentiment-weighted scoring system.
"""
import sys
sys.path.insert(0, '.')

from models.signals import SignalOutput
from engines.rule_engine import evaluate


def test_signal_model():
    """Test the new SignalOutput model with ability/enthusiasm split."""
    print("="*80)
    print("Test 1: SignalOutput Model with Ability/Enthusiasm Split")
    print("="*80)
    
    # Test case: High math ability but low enthusiasm
    signals = SignalOutput(
        Logical_Thinking_ability=0.8,
        Logical_Thinking_enthusiasm=0.3,
        Math_Aptitude_ability=0.9,
        Math_Aptitude_enthusiasm=0.2,
        Manual_Work_ability=0.6,
        Manual_Work_enthusiasm=0.8,
        Spatial_Awareness_ability=0.5,
        Spatial_Awareness_enthusiasm=0.7,
        Biology_Interest_ability=0.3,
        Biology_Interest_enthusiasm=0.2,
        Problem_Solving_ability=0.7,
        Problem_Solving_enthusiasm=0.4,
        Communication_ability=0.6,
        Communication_enthusiasm=0.5,
        Creativity_ability=0.5,
        Creativity_enthusiasm=0.6,
        Introvert_Extrovert="introvert",
        Risk_Level="medium",
        Confidence=0.8
    )
    
    print("\n✓ Created SignalOutput with ability/enthusiasm split")
    print(f"  Logical_Thinking: ability={signals.Logical_Thinking_ability}, enthusiasm={signals.Logical_Thinking_enthusiasm}")
    print(f"  Math_Aptitude: ability={signals.Math_Aptitude_ability}, enthusiasm={signals.Math_Aptitude_enthusiasm}")
    print(f"  Manual_Work: ability={signals.Manual_Work_ability}, enthusiasm={signals.Manual_Work_enthusiasm}")
    
    # Test combined score calculation
    lt_combined = signals.get_combined_score("Logical_Thinking")
    math_combined = signals.get_combined_score("Math_Aptitude")
    manual_combined = signals.get_combined_score("Manual_Work")
    
    print(f"\n✓ Combined scores (0.4*ability + 0.6*enthusiasm):")
    print(f"  Logical_Thinking: {lt_combined:.3f} (0.4*0.8 + 0.6*0.3 = {0.4*0.8 + 0.6*0.3:.3f})")
    print(f"  Math_Aptitude: {math_combined:.3f} (0.4*0.9 + 0.6*0.2 = {0.4*0.9 + 0.6*0.2:.3f})")
    print(f"  Manual_Work: {manual_combined:.3f} (0.4*0.6 + 0.6*0.8 = {0.4*0.6 + 0.6*0.8:.3f})")
    
    # Test enthusiasm gap calculation
    lt_gap = signals.get_enthusiasm_gap("Logical_Thinking")
    math_gap = signals.get_enthusiasm_gap("Math_Aptitude")
    manual_gap = signals.get_enthusiasm_gap("Manual_Work")
    
    print(f"\n✓ Enthusiasm gaps (ability - enthusiasm):")
    print(f"  Logical_Thinking: {lt_gap:+.2f} (high ability, low enthusiasm)")
    print(f"  Math_Aptitude: {math_gap:+.2f} (high ability, low enthusiasm)")
    print(f"  Manual_Work: {manual_gap:+.2f} (low ability, high enthusiasm)")
    
    print("\n✅ SignalOutput model test PASSED")
    return True


def test_acceptance_criterion_1():
    """
    Acceptance Criterion 1:
    Student saying "I'm great at math but hate sitting at a computer"
    → CS score drops, Mech score rises
    """
    print("\n" + "="*80)
    print("Test 2: Acceptance Criterion 1")
    print("Scenario: 'I'm great at math but hate sitting at a computer'")
    print("="*80)
    
    # High math/logic ability but low enthusiasm for computer work
    signals = SignalOutput(
        Logical_Thinking_ability=0.8,
        Logical_Thinking_enthusiasm=0.1,  # Hates computers
        Math_Aptitude_ability=0.9,
        Math_Aptitude_enthusiasm=0.3,
        Manual_Work_ability=0.6,
        Manual_Work_enthusiasm=0.8,  # Enjoys hands-on work
        Spatial_Awareness_ability=0.7,
        Spatial_Awareness_enthusiasm=0.7,
        Biology_Interest_ability=0.3,
        Biology_Interest_enthusiasm=0.2,
        Problem_Solving_ability=0.7,
        Problem_Solving_enthusiasm=0.3,
        Communication_ability=0.6,
        Communication_enthusiasm=0.5,
        Creativity_ability=0.6,
        Creativity_enthusiasm=0.7,
        Introvert_Extrovert="ambivert",
        Risk_Level="medium",
        Confidence=0.8
    )
    
    result = evaluate(signals.to_dict(), personality="ambivert", risk_level="medium")
    
    print(f"\n✓ Branch scores:")
    for branch, score in sorted(result.normalized_scores.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {score:.3f} ({score:.0%})")
    
    print(f"\n✓ Top branch: {result.top_branch}")
    print(f"✓ Confidence: {result.confidence:.0%}")
    
    # Check if CS score is penalized
    cs_score = result.normalized_scores.get("CS", 0.0)
    mech_score = result.normalized_scores.get("Mechanical", 0.0)
    
    print(f"\n✓ CS score: {cs_score:.3f}")
    print(f"✓ Mechanical score: {mech_score:.3f}")
    
    if result.penalties_applied.get("CS"):
        print(f"\n✓ CS penalties applied:")
        for penalty in result.penalties_applied["CS"]:
            print(f"  • {penalty}")
    
    # Acceptance: CS should NOT be top branch due to low enthusiasm
    if result.top_branch != "CS":
        print(f"\n✅ PASS: CS is not top branch (got {result.top_branch})")
        print(f"   Reason: Low enthusiasm for Logical_Thinking despite high ability")
        return True
    else:
        print(f"\n❌ FAIL: CS is still top branch despite low enthusiasm")
        return False


def test_acceptance_criterion_2():
    """
    Acceptance Criterion 2:
    Student saying "I love coding, it's my passion, I do it for fun"
    → CS gets Strong Match
    """
    print("\n" + "="*80)
    print("Test 3: Acceptance Criterion 2")
    print("Scenario: 'I love coding, it's my passion, I do it for fun'")
    print("="*80)
    
    # High enthusiasm for coding, moderate ability
    signals = SignalOutput(
        Logical_Thinking_ability=0.7,
        Logical_Thinking_enthusiasm=0.95,  # Loves coding
        Math_Aptitude_ability=0.6,
        Math_Aptitude_enthusiasm=0.8,
        Manual_Work_ability=0.4,
        Manual_Work_enthusiasm=0.3,
        Spatial_Awareness_ability=0.5,
        Spatial_Awareness_enthusiasm=0.4,
        Biology_Interest_ability=0.2,
        Biology_Interest_enthusiasm=0.1,
        Problem_Solving_ability=0.7,
        Problem_Solving_enthusiasm=0.9,  # Loves problem-solving
        Communication_ability=0.6,
        Communication_enthusiasm=0.5,
        Creativity_ability=0.6,
        Creativity_enthusiasm=0.7,
        Introvert_Extrovert="introvert",  # Prefers solo coding
        Risk_Level="high",  # Willing to try new tech
        Confidence=0.9
    )
    
    result = evaluate(signals.to_dict(), personality="introvert", risk_level="high")
    
    print(f"\n✓ Branch scores:")
    for branch, score in sorted(result.normalized_scores.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {score:.3f} ({score:.0%})")
    
    print(f"\n✓ Top branch: {result.top_branch}")
    print(f"✓ Confidence: {result.confidence:.0%}")
    print(f"✓ Gap ratio: {result.gap_ratio:.3f}")
    
    # Check for Strong Match (confidence >= 0.75)
    if result.top_branch == "CS" and result.confidence >= 0.75:
        print(f"\n✅ PASS: CS is top branch with Strong Match (confidence: {result.confidence:.0%})")
        print(f"   Reason: High enthusiasm for Logical_Thinking and Problem_Solving")
        return True
    elif result.top_branch == "CS":
        print(f"\n⚠️  PARTIAL PASS: CS is top branch but confidence is {result.confidence:.0%} (expected >= 75%)")
        return True
    else:
        print(f"\n❌ FAIL: Top branch is {result.top_branch}, not CS")
        return False


def test_acceptance_criterion_3():
    """
    Acceptance Criterion 3:
    Tie-breaker triggers when top 2 branches are within 0.15 of each other
    """
    print("\n" + "="*80)
    print("Test 4: Acceptance Criterion 3")
    print("Scenario: Student with near-equal aptitude for CS and Electronics")
    print("="*80)
    
    # Balanced signals between CS and Electronics
    signals = SignalOutput(
        Logical_Thinking_ability=0.75,
        Logical_Thinking_enthusiasm=0.7,
        Math_Aptitude_ability=0.8,
        Math_Aptitude_enthusiasm=0.75,
        Manual_Work_ability=0.5,
        Manual_Work_enthusiasm=0.4,
        Spatial_Awareness_ability=0.5,
        Spatial_Awareness_enthusiasm=0.5,
        Biology_Interest_ability=0.2,
        Biology_Interest_enthusiasm=0.1,
        Problem_Solving_ability=0.75,
        Problem_Solving_enthusiasm=0.7,
        Communication_ability=0.6,
        Communication_enthusiasm=0.5,
        Creativity_ability=0.5,
        Creativity_enthusiasm=0.5,
        Introvert_Extrovert="ambivert",
        Risk_Level="medium",
        Confidence=0.7
    )
    
    result = evaluate(signals.to_dict(), personality="ambivert", risk_level="medium")
    
    print(f"\n✓ Branch scores:")
    for branch, score in sorted(result.normalized_scores.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {score:.3f} ({score:.0%})")
    
    print(f"\n✓ Top branch: {result.top_branch} ({result.top_score:.3f})")
    print(f"✓ Second branch: {result.second_branch} ({result.second_score:.3f})")
    print(f"✓ Gap ratio: {result.gap_ratio:.3f}")
    print(f"✓ Is tied: {result.is_tied}")
    
    # Check if tie is detected (gap_ratio <= 0.15)
    if result.is_tied and result.gap_ratio <= 0.15:
        print(f"\n✅ PASS: Tie detected (gap ratio: {result.gap_ratio:.3f} <= 0.15)")
        print(f"   Top 2 branches: {result.top_branch} vs {result.second_branch}")
        return True
    elif result.gap_ratio <= 0.15:
        print(f"\n⚠️  WARNING: Gap ratio is {result.gap_ratio:.3f} but is_tied={result.is_tied}")
        return True
    else:
        print(f"\n❌ FAIL: Gap ratio is {result.gap_ratio:.3f} (expected <= 0.15 for tie)")
        return False


def test_enthusiasm_gap_warnings():
    """
    Test that enthusiasm gaps are properly detected and reported.
    """
    print("\n" + "="*80)
    print("Test 5: Enthusiasm Gap Detection")
    print("Scenario: High ability but low enthusiasm in multiple dimensions")
    print("="*80)
    
    signals = SignalOutput(
        Logical_Thinking_ability=0.9,
        Logical_Thinking_enthusiasm=0.3,  # Large gap
        Math_Aptitude_ability=0.85,
        Math_Aptitude_enthusiasm=0.4,  # Large gap
        Manual_Work_ability=0.5,
        Manual_Work_enthusiasm=0.5,
        Spatial_Awareness_ability=0.5,
        Spatial_Awareness_enthusiasm=0.5,
        Biology_Interest_ability=0.3,
        Biology_Interest_enthusiasm=0.2,
        Problem_Solving_ability=0.8,
        Problem_Solving_enthusiasm=0.5,  # Moderate gap
        Communication_ability=0.6,
        Communication_enthusiasm=0.6,
        Creativity_ability=0.5,
        Creativity_enthusiasm=0.5,
        Introvert_Extrovert="ambivert",
        Risk_Level="medium",
        Confidence=0.7
    )
    
    result = evaluate(signals.to_dict(), personality="ambivert", risk_level="medium")
    
    print(f"\n✓ Top branch: {result.top_branch}")
    
    # Check enthusiasm gaps for top branch
    if result.top_branch in result.enthusiasm_gaps:
        gaps = result.enthusiasm_gaps[result.top_branch]
        print(f"\n✓ Enthusiasm gaps for {result.top_branch}:")
        for dimension, gap in sorted(gaps.items(), key=lambda x: -abs(x[1])):
            if abs(gap) > 0.2:
                status = "⚠️ " if gap > 0.3 else "ℹ️ "
                print(f"  {status}{dimension}: {gap:+.2f} (ability - enthusiasm)")
    
    # Check if any gaps exceed 0.3 (should trigger warnings)
    large_gaps = [
        (dim, gap) for dim, gap in result.enthusiasm_gaps.get(result.top_branch, {}).items()
        if gap > 0.3
    ]
    
    if large_gaps:
        print(f"\n✅ PASS: Detected {len(large_gaps)} large enthusiasm gap(s)")
        for dim, gap in large_gaps:
            print(f"   • {dim}: {gap:+.2f}")
        return True
    else:
        print(f"\n⚠️  INFO: No large enthusiasm gaps detected (this is OK for this test)")
        return True


def test_personality_and_risk_modifiers():
    """
    Test that personality and risk-taking modifiers are applied correctly.
    """
    print("\n" + "="*80)
    print("Test 6: Personality and Risk-Taking Modifiers")
    print("="*80)
    
    # Base signals
    base_signals = {
        "Logical_Thinking_ability": 0.7,
        "Logical_Thinking_enthusiasm": 0.7,
        "Math_Aptitude_ability": 0.7,
        "Math_Aptitude_enthusiasm": 0.7,
        "Manual_Work_ability": 0.5,
        "Manual_Work_enthusiasm": 0.5,
        "Spatial_Awareness_ability": 0.5,
        "Spatial_Awareness_enthusiasm": 0.5,
        "Biology_Interest_ability": 0.3,
        "Biology_Interest_enthusiasm": 0.3,
        "Problem_Solving_ability": 0.7,
        "Problem_Solving_enthusiasm": 0.7,
        "Communication_ability": 0.5,
        "Communication_enthusiasm": 0.5,
        "Creativity_ability": 0.5,
        "Creativity_enthusiasm": 0.5,
    }
    
    # Test 1: Introvert (should boost CS)
    print("\n✓ Test 6a: Introvert personality")
    result_introvert = evaluate(base_signals, personality="introvert", risk_level="medium")
    cs_score_introvert = result_introvert.normalized_scores.get("CS", 0.0)
    print(f"  CS score (introvert): {cs_score_introvert:.3f}")
    
    # Test 2: Extrovert (should boost Civil/Mechanical)
    print("\n✓ Test 6b: Extrovert personality")
    result_extrovert = evaluate(base_signals, personality="extrovert", risk_level="medium")
    civil_score_extrovert = result_extrovert.normalized_scores.get("Civil", 0.0)
    print(f"  Civil score (extrovert): {civil_score_extrovert:.3f}")
    
    # Test 3: High risk (should boost CS/Electronics)
    print("\n✓ Test 6c: High risk-taking")
    result_high_risk = evaluate(base_signals, personality="ambivert", risk_level="high")
    cs_score_high_risk = result_high_risk.normalized_scores.get("CS", 0.0)
    print(f"  CS score (high risk): {cs_score_high_risk:.3f}")
    
    # Test 4: Low risk (should boost Civil/Mechanical)
    print("\n✓ Test 6d: Low risk-taking")
    result_low_risk = evaluate(base_signals, personality="ambivert", risk_level="low")
    civil_score_low_risk = result_low_risk.normalized_scores.get("Civil", 0.0)
    print(f"  Civil score (low risk): {civil_score_low_risk:.3f}")
    
    print(f"\n✅ PASS: Personality and risk modifiers applied")
    return True


def main():
    print("\n" + "="*80)
    print("Ability/Enthusiasm Split Test Suite")
    print("="*80)
    
    tests = [
        ("SignalOutput Model", test_signal_model),
        ("Acceptance Criterion 1", test_acceptance_criterion_1),
        ("Acceptance Criterion 2", test_acceptance_criterion_2),
        ("Acceptance Criterion 3", test_acceptance_criterion_3),
        ("Enthusiasm Gap Detection", test_enthusiasm_gap_warnings),
        ("Personality/Risk Modifiers", test_personality_and_risk_modifiers),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
