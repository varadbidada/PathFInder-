"""
engines/rule_engine.py — Multi-Signal Sentiment-Weighted Branch Scorer

Enhanced with ability/enthusiasm split:
- Each signal has TWO dimensions: ability (skill) and enthusiasm (passion)
- Scoring formula: 0.4 * ability + 0.6 * enthusiasm
- Minimum enthusiasm threshold: enthusiasm < 0.2 → -0.3 penalty
- Personality fit: introvert/extrovert preferences
- Risk-taking: high risk → prefer emerging branches

All decisions are auditable, explainable, and unit-testable.
No AI makes the final branch call — this engine does.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from config import settings


# ── Branch requirements (core dimensions + minimum enthusiasm thresholds) ─────

BRANCH_REQUIREMENTS: dict[str, dict[str, tuple[str, float]]] = {
    "CS": {
        "Logical_Thinking": ("enthusiasm", 0.2),  # Must enjoy logic/coding
        "Math_Aptitude": ("enthusiasm", 0.15),    # Should tolerate math
        "Problem_Solving": ("enthusiasm", 0.2),   # Must enjoy debugging
    },
    "Electronics": {
        "Logical_Thinking": ("enthusiasm", 0.15),
        "Math_Aptitude": ("enthusiasm", 0.2),
        "Problem_Solving": ("enthusiasm", 0.15),
    },
    "Mechanical": {
        "Manual_Work": ("enthusiasm", 0.2),       # Must enjoy hands-on work
        "Spatial_Awareness": ("enthusiasm", 0.15),
        "Creativity": ("enthusiasm", 0.1),
    },
    "Civil": {
        "Spatial_Awareness": ("enthusiasm", 0.2),
        "Manual_Work": ("enthusiasm", 0.15),
        "Communication": ("enthusiasm", 0.1),     # Team projects
    },
    "Medical": {
        "Biology_Interest": ("enthusiasm", 0.3),  # Must love biology
        "Communication": ("enthusiasm", 0.15),    # Patient interaction
    },
}

# ── Signal → Branch weight map (ability + enthusiasm combined) ───────────────

SIGNAL_BRANCH_WEIGHTS: dict[str, dict[str, tuple[float, float]]] = {
    # Format: dimension → {branch: (ability_weight, enthusiasm_weight)}
    "Logical_Thinking": {
        "CS": (2.5, 3.5),           # CS heavily weights enthusiasm
        "Electronics": (1.5, 2.0),
    },
    "Creativity": {
        "Civil": (1.5, 2.0),
        "Mechanical": (1.0, 1.5),
    },
    "Manual_Work": {
        "Mechanical": (2.0, 3.0),
        "Civil": (1.5, 2.0),
        "Electronics": (0.5, 1.0),
    },
    "Spatial_Awareness": {
        "Civil": (2.0, 2.5),
        "Mechanical": (1.5, 2.0),
    },
    "Biology_Interest": {
        "Medical": (2.0, 3.0),
    },
    "Problem_Solving": {
        "CS": (2.0, 2.5),
        "Electronics": (1.5, 2.0),
        "Mechanical": (0.5, 1.0),
    },
    "Communication": {
        "Civil": (0.5, 1.0),
        "Medical": (1.0, 1.5),
    },
    "Math_Aptitude": {
        "CS": (1.5, 2.0),
        "Electronics": (2.0, 2.5),
        "Mechanical": (0.5, 1.0),
    },
}

# ── Personality fit modifiers ─────────────────────────────────────────────────

PERSONALITY_MODIFIERS: dict[str, dict[str, float]] = {
    "introvert": {
        "CS": 0.15,              # Research-oriented, solo coding
        "Electronics": 0.10,     # Lab work, individual projects
    },
    "extrovert": {
        "Civil": 0.15,           # Team projects, site management
        "Mechanical": 0.10,      # Factory floor, team coordination
        "Medical": 0.10,         # Patient interaction
    },
    "ambivert": {},              # No modifiers
}

RISK_MODIFIERS: dict[str, dict[str, float]] = {
    "high": {
        "CS": 0.10,              # Emerging fields: AI/ML, startups
        "Electronics": 0.05,     # IoT, embedded systems
    },
    "low": {
        "Civil": 0.10,           # Stable government jobs
        "Mechanical": 0.05,      # Traditional manufacturing
    },
    "medium": {},                # No modifiers
}

ALL_BRANCHES: list[str] = ["CS", "Electronics", "Mechanical", "Civil", "Medical"]


@dataclass
class ScoreResult:
    raw_scores: dict[str, float]
    normalized_scores: dict[str, float]
    top_branch: str
    second_branch: str
    top_score: float
    second_score: float
    gap_ratio: float
    is_tied: bool
    confidence: float
    explanation: str
    signal_breakdown: dict[str, dict[str, float]] = field(default_factory=dict)
    enthusiasm_gaps: dict[str, dict[str, float]] = field(default_factory=dict)
    penalties_applied: dict[str, list[str]] = field(default_factory=dict)


def compute_branch_scores(
    signals: dict[str, float],
    personality: str = "ambivert",
    risk_level: str = "medium",
) -> tuple[dict[str, float], dict[str, dict[str, float]], dict[str, dict[str, float]], dict[str, list[str]]]:
    """
    Apply the ability/enthusiasm weighted scoring formula.
    
    Returns:
        - raw_scores: dict[branch, score]
        - signal_breakdown: dict[branch, dict[dimension, contribution]]
        - enthusiasm_gaps: dict[branch, dict[dimension, gap]]
        - penalties_applied: dict[branch, list[reason]]
    """
    scores: dict[str, float] = {branch: 0.0 for branch in ALL_BRANCHES}
    breakdown: dict[str, dict[str, float]] = {branch: {} for branch in ALL_BRANCHES}
    gaps: dict[str, dict[str, float]] = {branch: {} for branch in ALL_BRANCHES}
    penalties: dict[str, list[str]] = {branch: [] for branch in ALL_BRANCHES}
    
    # Step 1: Compute base scores from ability + enthusiasm
    for dimension, branch_weights in SIGNAL_BRANCH_WEIGHTS.items():
        ability_key = f"{dimension}_ability"
        enthusiasm_key = f"{dimension}_enthusiasm"
        
        ability = signals.get(ability_key, 0.5)
        enthusiasm = signals.get(enthusiasm_key, 0.5)
        
        for branch, (ability_weight, enthusiasm_weight) in branch_weights.items():
            if branch in scores:
                # Formula: 0.4 * ability + 0.6 * enthusiasm (weighted by branch-specific weights)
                contribution = (0.4 * ability * ability_weight) + (0.6 * enthusiasm * enthusiasm_weight)
                scores[branch] += contribution
                breakdown[branch][dimension] = contribution
                gaps[branch][dimension] = ability - enthusiasm
    
    # Step 2: Apply minimum enthusiasm threshold penalties
    for branch, requirements in BRANCH_REQUIREMENTS.items():
        for dimension, (signal_type, threshold) in requirements.items():
            signal_key = f"{dimension}_{signal_type}"
            signal_value = signals.get(signal_key, 0.5)
            
            if signal_value < threshold:
                penalty = -0.3
                scores[branch] += penalty
                penalties[branch].append(
                    f"{dimension} {signal_type} too low ({signal_value:.2f} < {threshold:.2f}): {penalty:.2f}"
                )
    
    # Step 3: Apply personality fit modifiers
    personality_mods = PERSONALITY_MODIFIERS.get(personality, {})
    for branch, modifier in personality_mods.items():
        if branch in scores:
            scores[branch] += modifier
            breakdown[branch]["personality_fit"] = modifier
    
    # Step 4: Apply risk-taking modifiers
    risk_mods = RISK_MODIFIERS.get(risk_level, {})
    for branch, modifier in risk_mods.items():
        if branch in scores:
            scores[branch] += modifier
            breakdown[branch]["risk_fit"] = modifier
    
    return scores, breakdown, gaps, penalties


def normalize_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    """
    Normalize branch scores to [0, 1] range.
    Uses min-max normalization to preserve relative differences.
    """
    if not raw_scores:
        return {branch: 0.0 for branch in ALL_BRANCHES}
    
    min_score = min(raw_scores.values())
    max_score = max(raw_scores.values())
    
    if max_score == min_score:
        # All scores equal → return 0.5 for all
        return {branch: 0.5 for branch in ALL_BRANCHES}
    
    normalized: dict[str, float] = {}
    for branch in ALL_BRANCHES:
        raw = raw_scores.get(branch, 0.0)
        normalized[branch] = round((raw - min_score) / (max_score - min_score), 4)
    
    return normalized


def detect_tie(
    normalized_scores: dict[str, float],
    threshold: float | None = None,
) -> tuple[str, str, float, bool]:
    """
    Identify top-2 branches and whether they are within a tie threshold.
    Returns (top_branch, second_branch, gap_ratio, is_tied).
    """
    if threshold is None:
        threshold = settings.tie_threshold

    sorted_branches = sorted(
        normalized_scores.items(), key=lambda x: x[1], reverse=True
    )
    top_branch, top_score = sorted_branches[0]
    second_branch, second_score = sorted_branches[1] if len(sorted_branches) > 1 else (top_branch, 0.0)

    denominator = top_score if top_score > 0 else 1.0
    gap_ratio = (top_score - second_score) / denominator
    is_tied = gap_ratio <= threshold

    return top_branch, second_branch, round(gap_ratio, 4), is_tied


def compute_confidence(
    normalized_scores: dict[str, float],
    top_branch: str,
    gap_ratio: float,
) -> tuple[float, str]:
    """
    Compute an overall confidence score [0.0, 1.0] and confidence label.
    
    Returns:
        - confidence: float [0.0, 1.0]
        - label: "Strong Match" | "Good Match" | "Moderate Match" | "Weak Match"
    """
    top_score = normalized_scores.get(top_branch, 0.0)
    
    # Weight: 60% absolute score, 40% gap separation
    confidence = (top_score * 0.6) + (min(gap_ratio, 1.0) * 0.4)
    confidence = round(min(confidence, 1.0), 4)
    
    # Confidence labels
    if confidence >= 0.75:
        label = "Strong Match"
    elif confidence >= 0.60:
        label = "Good Match"
    elif confidence >= 0.40:
        label = "Moderate Match"
    else:
        label = "Weak Match"
    
    return confidence, label


def build_explanation(
    normalized_scores: dict[str, float],
    top_branch: str,
    is_tied: bool,
    second_branch: str,
    confidence_label: str,
) -> str:
    score_lines = ", ".join(
        f"{b}: {v:.0%}" for b, v in sorted(normalized_scores.items(), key=lambda x: -x[1])
    )
    if is_tied:
        return (
            f"Your profile shows near-equal aptitude for {top_branch} ({normalized_scores[top_branch]:.0%}) "
            f"and {second_branch} ({normalized_scores.get(second_branch, 0):.0%}). "
            f"A tie-breaker question will help clarify. [{score_lines}]"
        )
    return (
        f"{top_branch} emerges as your strongest match ({normalized_scores[top_branch]:.0%}) — {confidence_label}. "
        f"Full scores: [{score_lines}]"
    )


def evaluate(signals: dict[str, float], personality: str = "ambivert", risk_level: str = "medium") -> ScoreResult:
    """
    Main entry: run full scoring pipeline with ability/enthusiasm weighting.
    Returns a ScoreResult with all intermediate values for auditability.
    """
    raw, breakdown, gaps, penalties = compute_branch_scores(signals, personality, risk_level)
    normalized = normalize_scores(raw)
    top_branch, second_branch, gap_ratio, is_tied = detect_tie(normalized)
    top_score = normalized.get(top_branch, 0.0)
    second_score = normalized.get(second_branch, 0.0)
    confidence, confidence_label = compute_confidence(normalized, top_branch, gap_ratio)
    explanation = build_explanation(normalized, top_branch, is_tied, second_branch, confidence_label)

    return ScoreResult(
        raw_scores=raw,
        normalized_scores=normalized,
        top_branch=top_branch,
        second_branch=second_branch,
        top_score=top_score,
        second_score=second_score,
        gap_ratio=gap_ratio,
        is_tied=is_tied,
        confidence=confidence,
        explanation=explanation,
        signal_breakdown=breakdown,
        enthusiasm_gaps=gaps,
        penalties_applied=penalties,
    )
