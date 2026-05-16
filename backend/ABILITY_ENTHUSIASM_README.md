# Multi-Signal Sentiment-Weighted Scoring System

## Overview

This document describes the enhanced branch prediction system that uses **ability/enthusiasm split** to provide more accurate career recommendations. The system recognizes that **enthusiasm predicts long-term career satisfaction better than raw ability alone**.

## Problem Statement

### Old System (Keyword-Based)

```python
# Single signal per dimension
Math_Aptitude: 0.9  # High score

# Problem: Student says "I'm good at math but I find it boring"
# Result: High Math_Aptitude → CS recommendation (WRONG!)
```

### New System (Ability/Enthusiasm Split)

```python
# Dual signals per dimension
Math_Aptitude_ability: 0.9      # How good they are
Math_Aptitude_enthusiasm: 0.2   # How much they enjoy it

# Scoring: 0.4 * ability + 0.6 * enthusiasm = 0.4*0.9 + 0.6*0.2 = 0.48
# Result: Lower combined score → CS recommendation drops (CORRECT!)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Signal Extraction (Groq LLM)                    │
├─────────────────────────────────────────────────────────────────┤
│  Input: "I'm great at math but hate sitting at a computer"      │
│                                                                   │
│  Output:                                                          │
│    Logical_Thinking_ability: 0.8                                 │
│    Logical_Thinking_enthusiasm: 0.1  ← Low!                      │
│    Math_Aptitude_ability: 0.9                                    │
│    Math_Aptitude_enthusiasm: 0.3                                 │
│    Manual_Work_ability: 0.6                                      │
│    Manual_Work_enthusiasm: 0.8  ← High!                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Rule Engine Scoring                           │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Compute combined scores                                 │
│    Formula: 0.4 * ability + 0.6 * enthusiasm                     │
│                                                                   │
│  Step 2: Apply minimum enthusiasm thresholds                     │
│    CS requires Logical_Thinking_enthusiasm > 0.2                 │
│    If below threshold → -0.3 penalty                             │
│                                                                   │
│  Step 3: Apply personality fit modifiers                         │
│    Introvert → +0.15 to CS (research-oriented)                   │
│    Extrovert → +0.15 to Civil (team projects)                    │
│                                                                   │
│  Step 4: Apply risk-taking modifiers                             │
│    High risk → +0.10 to CS (emerging fields)                     │
│    Low risk → +0.10 to Civil (stable jobs)                       │
│                                                                   │
│  Result:                                                          │
│    CS: 0.436 (44%) ← Penalized for low enthusiasm                │
│    Mechanical: 1.000 (100%) ← Boosted by high Manual_Work        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Confidence Scoring                             │
├─────────────────────────────────────────────────────────────────┤
│  confidence = 0.6 * top_score + 0.4 * gap_ratio                  │
│                                                                   │
│  Labels:                                                          │
│    ≥ 0.75 → "Strong Match"                                       │
│    ≥ 0.60 → "Good Match"                                         │
│    ≥ 0.40 → "Moderate Match"                                     │
│    < 0.40 → "Weak Match"                                         │
│                                                                   │
│  Tie Detection:                                                   │
│    gap_ratio ≤ 0.15 → Trigger tie-breaker question               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Explanation Generation                          │
├─────────────────────────────────────────────────────────────────┤
│  • Top branch with confidence label                              │
│  • Signal breakdown (which dimensions drove the score)           │
│  • Enthusiasm gap warnings                                       │
│  • Penalties applied (if any)                                    │
│                                                                   │
│  Example:                                                         │
│    "Mechanical Engineering — Strong Match (100% match, 62%       │
│     confidence)                                                   │
│                                                                   │
│     ✓ Strong in: Manual Work, Spatial Awareness                  │
│                                                                   │
│     ⚠️ Logical Thinking: High ability (80%) but low enthusiasm   │
│        (10%). Consider if you'd enjoy this long-term."           │
└─────────────────────────────────────────────────────────────────┘
```

## Signal Dimensions

Each dimension is split into **ability** (skill level) and **enthusiasm** (passion/enjoyment):

| Dimension             | Ability                           | Enthusiasm                           |
| --------------------- | --------------------------------- | ------------------------------------ |
| **Logical_Thinking**  | How good at coding/algorithms     | How much they enjoy logic puzzles    |
| **Creativity**        | How good at design/innovation     | How much they enjoy creative work    |
| **Manual_Work**       | How good at hands-on building     | How much they enjoy physical work    |
| **Spatial_Awareness** | How good at 3D visualization      | How much they enjoy spatial problems |
| **Biology_Interest**  | How good at life sciences         | How much they enjoy biology          |
| **Problem_Solving**   | How good at debugging             | How much they enjoy solving problems |
| **Communication**     | How good at teamwork/presentation | How much they enjoy communication    |
| **Math_Aptitude**     | How good at calculus/algebra      | How much they enjoy mathematics      |

### Additional Dimensions

- **Introvert_Extrovert**: `"introvert"` | `"ambivert"` | `"extrovert"`
  - Introvert: Prefers solo work, research-oriented
  - Extrovert: Prefers teamwork, leadership roles
- **Risk_Level**: `"low"` | `"medium"` | `"high"`
  - Low: Risk-averse, prefers stable careers
  - High: Ambitious, willing to try emerging fields

## Scoring Formula

### Base Score Calculation

```python
# For each dimension:
combined_score = 0.4 * ability + 0.6 * enthusiasm

# Example:
Math_Aptitude_ability = 0.9
Math_Aptitude_enthusiasm = 0.2
combined = 0.4 * 0.9 + 0.6 * 0.2 = 0.48

# Rationale: Enthusiasm (60%) > Ability (40%)
# A student who loves something will develop the ability.
# The reverse rarely holds.
```

### Branch-Specific Weights

```python
SIGNAL_BRANCH_WEIGHTS = {
    "Logical_Thinking": {
        "CS": (2.5, 3.5),           # (ability_weight, enthusiasm_weight)
        "Electronics": (1.5, 2.0),
    },
    "Manual_Work": {
        "Mechanical": (2.0, 3.0),
        "Civil": (1.5, 2.0),
    },
    # ... etc
}

# CS score calculation:
cs_score = (
    (0.4 * Logical_Thinking_ability * 2.5) + (0.6 * Logical_Thinking_enthusiasm * 3.5) +
    (0.4 * Math_Aptitude_ability * 1.5) + (0.6 * Math_Aptitude_enthusiasm * 2.0) +
    # ... other dimensions
)
```

### Minimum Enthusiasm Thresholds

```python
BRANCH_REQUIREMENTS = {
    "CS": {
        "Logical_Thinking": ("enthusiasm", 0.2),  # Must enjoy logic/coding
        "Math_Aptitude": ("enthusiasm", 0.15),
        "Problem_Solving": ("enthusiasm", 0.2),
    },
    "Mechanical": {
        "Manual_Work": ("enthusiasm", 0.2),       # Must enjoy hands-on work
        "Spatial_Awareness": ("enthusiasm", 0.15),
    },
    # ... etc
}

# If enthusiasm < threshold → -0.3 penalty
# Example: CS requires Logical_Thinking_enthusiasm > 0.2
# If student has 0.1 → CS score -= 0.3
```

### Personality Fit Modifiers

```python
PERSONALITY_MODIFIERS = {
    "introvert": {
        "CS": +0.15,              # Research-oriented, solo coding
        "Electronics": +0.10,     # Lab work, individual projects
    },
    "extrovert": {
        "Civil": +0.15,           # Team projects, site management
        "Mechanical": +0.10,      # Factory floor, team coordination
        "Medical": +0.10,         # Patient interaction
    },
}
```

### Risk-Taking Modifiers

```python
RISK_MODIFIERS = {
    "high": {
        "CS": +0.10,              # Emerging fields: AI/ML, startups
        "Electronics": +0.05,     # IoT, embedded systems
    },
    "low": {
        "Civil": +0.10,           # Stable government jobs
        "Mechanical": +0.05,      # Traditional manufacturing
    },
}
```

## Confidence Scoring

```python
# Step 1: Normalize scores to [0, 1]
normalized_scores = min_max_normalize(raw_scores)

# Step 2: Compute gap ratio
gap_ratio = (top_score - second_score) / top_score

# Step 3: Compute confidence
confidence = 0.6 * top_score + 0.4 * gap_ratio

# Step 4: Assign label
if confidence >= 0.75:
    label = "Strong Match"
elif confidence >= 0.60:
    label = "Good Match"
elif confidence >= 0.40:
    label = "Moderate Match"
else:
    label = "Weak Match"

# Step 5: Check for tie
if gap_ratio <= 0.15:
    is_tied = True  # Trigger tie-breaker question
```

## Acceptance Criteria

### ✅ Criterion 1: High Ability, Low Enthusiasm → Score Drops

**Input**: "I'm great at math but hate sitting at a computer"

**Signals**:

```python
Logical_Thinking_ability: 0.8
Logical_Thinking_enthusiasm: 0.1  # Low!
Math_Aptitude_ability: 0.9
Math_Aptitude_enthusiasm: 0.3
Manual_Work_ability: 0.6
Manual_Work_enthusiasm: 0.8  # High!
```

**Result**:

```
CS: 0.436 (44%) ← Penalized for low enthusiasm
Mechanical: 1.000 (100%) ← Boosted by high Manual_Work enthusiasm
```

**Explanation**: CS score drops despite high math/logic ability because enthusiasm is low. Mechanical rises due to high enthusiasm for hands-on work.

### ✅ Criterion 2: High Enthusiasm → Strong Match

**Input**: "I love coding, it's my passion, I do it for fun"

**Signals**:

```python
Logical_Thinking_ability: 0.7
Logical_Thinking_enthusiasm: 0.95  # Very high!
Problem_Solving_ability: 0.7
Problem_Solving_enthusiasm: 0.9  # Very high!
Introvert_Extrovert: "introvert"  # Prefers solo coding
Risk_Level: "high"  # Willing to try new tech
```

**Result**:

```
CS: 1.000 (100%) — Good Match (68% confidence)
```

**Explanation**: CS gets top score due to very high enthusiasm for coding and problem-solving, plus introvert personality fit and high risk-taking.

### ✅ Criterion 3: Tie Detection → Tie-Breaker Question

**Input**: Student with balanced signals between CS and Electronics

**Signals**:

```python
Logical_Thinking_ability: 0.75
Logical_Thinking_enthusiasm: 0.7
Math_Aptitude_ability: 0.8
Math_Aptitude_enthusiasm: 0.75
Problem_Solving_ability: 0.75
Problem_Solving_enthusiasm: 0.7
```

**Result**:

```
CS: 1.000 (100%)
Electronics: 0.875 (88%)
Gap ratio: 0.125 ← Below 0.15 threshold
Is tied: True ← Trigger tie-breaker
```

**Explanation**: Top 2 branches are within 0.15 of each other, so a tie-breaker question is triggered to help differentiate.

## Enthusiasm Gap Warnings

The system detects when ability is significantly higher than enthusiasm (gap > 0.3) and provides warnings:

```python
# Example: High ability but low enthusiasm
Logical_Thinking_ability: 0.9
Logical_Thinking_enthusiasm: 0.3
gap = 0.9 - 0.3 = 0.6  # Large gap!

# Warning generated:
"⚠️ Logical Thinking: High ability (90%) but low enthusiasm (30%).
   Consider if you'd enjoy this long-term."
```

These warnings help students make informed decisions about branches where they might excel academically but struggle with long-term satisfaction.

## Signal Breakdown

The system provides transparency by showing which signals drove each branch recommendation:

```python
# Example for CS branch:
signal_breakdown = {
    "Logical_Thinking": 2.85,      # Highest contributor
    "Problem_Solving": 2.10,
    "Math_Aptitude": 1.44,
    "personality_fit": 0.15,       # Introvert bonus
    "risk_fit": 0.10,              # High risk bonus
}

# Formatted output:
"✓ Strong in: Logical Thinking, Problem Solving, Math Aptitude"
```

## API Changes

### SignalOutput Model

**Old**:

```python
class SignalOutput(BaseModel):
    Logical_Thinking: float
    Math_Aptitude: float
    # ... etc
```

**New**:

```python
class SignalOutput(BaseModel):
    Logical_Thinking_ability: float
    Logical_Thinking_enthusiasm: float
    Math_Aptitude_ability: float
    Math_Aptitude_enthusiasm: float
    # ... etc
    Introvert_Extrovert: Literal["introvert", "ambivert", "extrovert"]
    Risk_Level: Literal["low", "medium", "high"]
```

### Rule Engine

**Old**:

```python
result = evaluate(signals: dict[str, float]) -> ScoreResult
```

**New**:

```python
result = evaluate(
    signals: dict[str, float],
    personality: str = "ambivert",
    risk_level: str = "medium"
) -> ScoreResult

# ScoreResult now includes:
# - signal_breakdown: dict[branch, dict[dimension, contribution]]
# - enthusiasm_gaps: dict[branch, dict[dimension, gap]]
# - penalties_applied: dict[branch, list[reason]]
```

### Explanation Service

**Old**:

```python
build_branch_summary(result: ScoreResult) -> str
```

**New**:

```python
build_branch_summary(
    result: ScoreResult,
    signals: SignalOutput | None = None
) -> str

# Now includes:
# - Confidence label ("Strong Match", "Good Match", etc.)
# - Signal breakdown (which dimensions drove the score)
# - Enthusiasm gap warnings
# - Penalties applied
```

## Testing

Run the test suite:

```bash
python scripts/test_ability_enthusiasm.py
```

**Test Coverage**:

1. ✅ SignalOutput model with ability/enthusiasm split
2. ✅ Acceptance Criterion 1: High ability, low enthusiasm → score drops
3. ✅ Acceptance Criterion 2: High enthusiasm → Strong Match
4. ✅ Acceptance Criterion 3: Tie detection → tie-breaker
5. ✅ Enthusiasm gap detection and warnings
6. ✅ Personality and risk-taking modifiers

**Expected Output**:

```
Total: 6
Passed: 6
Failed: 0

✅ ALL TESTS PASSED!
```

## Migration Guide

### For Frontend Developers

**Old API Response**:

```json
{
  "recommended_branch": "CS",
  "branch_scores": {
    "CS": 0.85,
    "Electronics": 0.72
  },
  "confidence": 0.78
}
```

**New API Response**:

```json
{
  "recommended_branch": "CS",
  "branch_scores": {
    "CS": 0.85,
    "Electronics": 0.72
  },
  "confidence": 0.78,
  "branch_summary": "CS Engineering — Strong Match (85% match, 78% confidence)\n\n✓ Strong in: Logical Thinking, Problem Solving\n\n⚠️ Math Aptitude: High ability (90%) but low enthusiasm (30%). Consider if you'd enjoy this long-term."
}
```

### For Backend Developers

**Old Signal Extraction**:

```python
# ai_service.py
signals = await extract_signals(user_answer, question)
# Returns: SignalOutput with single values per dimension
```

**New Signal Extraction**:

```python
# ai_service.py
signals = await extract_signals(user_answer, question)
# Returns: SignalOutput with ability/enthusiasm split

# Access values:
ability = signals.Logical_Thinking_ability
enthusiasm = signals.Logical_Thinking_enthusiasm
combined = signals.get_combined_score("Logical_Thinking")
gap = signals.get_enthusiasm_gap("Logical_Thinking")
```

**Old Rule Engine Call**:

```python
result = evaluate(signals.to_dict())
```

**New Rule Engine Call**:

```python
result = evaluate(
    signals.to_dict(),
    personality=signals.Introvert_Extrovert,
    risk_level=signals.Risk_Level
)

# Access new fields:
breakdown = result.signal_breakdown["CS"]
gaps = result.enthusiasm_gaps["CS"]
penalties = result.penalties_applied["CS"]
```

## Design Rationale

### Why 0.4 _ ability + 0.6 _ enthusiasm?

**Research shows**:

- Enthusiasm predicts long-term career satisfaction better than raw ability
- Students who love something will develop the ability over time
- Students who are good at something but hate it will burn out

**Example**:

- Student A: High math ability (0.9), low enthusiasm (0.2) → Combined: 0.48
- Student B: Moderate math ability (0.6), high enthusiasm (0.9) → Combined: 0.78
- **Student B is more likely to succeed long-term** despite lower current ability

### Why minimum enthusiasm thresholds?

**Problem**: A student might have high ability in a dimension but zero enthusiasm.

**Solution**: Set minimum enthusiasm thresholds for core requirements.

**Example**:

- CS requires `Logical_Thinking_enthusiasm > 0.2`
- If student has 0.1 → Apply -0.3 penalty
- **Rationale**: If you hate coding, you won't enjoy CS regardless of ability

### Why personality and risk-taking modifiers?

**Personality fit**:

- Introverts thrive in research-oriented branches (CS, Electronics)
- Extroverts thrive in team-oriented branches (Civil, Mechanical, Medical)

**Risk-taking**:

- High risk-takers prefer emerging fields (AI/ML, startups)
- Low risk-takers prefer stable careers (government jobs, traditional manufacturing)

**Impact**: Small modifiers (+0.10 to +0.15) that can tip the balance in close cases.

## Future Enhancements

1. **Dynamic Weight Learning**: Learn optimal weights from student feedback
2. **Temporal Analysis**: Track how enthusiasm changes over time
3. **Peer Comparison**: Compare student's enthusiasm profile with successful alumni
4. **Intervention Triggers**: Flag students at risk of burnout (high ability, low enthusiasm)
5. **Multi-Branch Recommendations**: Suggest 2-3 branches instead of just one

## References

- [Self-Determination Theory](https://selfdeterminationtheory.org/) - Intrinsic motivation research
- [Flow Theory](<https://en.wikipedia.org/wiki/Flow_(psychology)>) - Optimal experience in work
- [Career Satisfaction Research](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6124958/) - Passion vs. ability

## License

Part of the Pathfinder project. See main README for license information.
