"""
engines/rule_engine.py — Deterministic Branch Scorer
All decisions are auditable, explainable, and unit-testable.
No AI makes the final branch call — this engine does.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from config import settings


# ── Signal → Branch weight map (sourced from config) ─────────────────────────
SIGNAL_BRANCH_MAP: dict[str, dict[str, float]] = settings.SIGNAL_BRANCH_MAP

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


def compute_branch_scores(signals: dict[str, float]) -> dict[str, float]:
    """
    Apply the SIGNAL_BRANCH_MAP weights to signal values.
    Returns raw (un-normalized) branch scores.
    """
    scores: dict[str, float] = {branch: 0.0 for branch in ALL_BRANCHES}
    for signal_name, signal_value in signals.items():
        branch_weights = SIGNAL_BRANCH_MAP.get(signal_name, {})
        for branch, weight in branch_weights.items():
            if branch in scores:
                scores[branch] += signal_value * weight
    return scores


def normalize_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    """Normalize branch scores to [0, 1] range by dividing by max possible score."""
    # Max possible score per branch = sum of all weights for that branch (with signal=1.0)
    max_possible: dict[str, float] = {branch: 0.0 for branch in ALL_BRANCHES}
    for signal_weights in SIGNAL_BRANCH_MAP.values():
        for branch, weight in signal_weights.items():
            if branch in max_possible:
                max_possible[branch] += weight

    normalized: dict[str, float] = {}
    for branch in ALL_BRANCHES:
        max_val = max_possible.get(branch, 1.0)
        if max_val == 0:
            normalized[branch] = 0.0
        else:
            normalized[branch] = round(raw_scores.get(branch, 0.0) / max_val, 4)
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
) -> float:
    """
    Compute an overall confidence score [0.0, 1.0].
    Factors: absolute top score + separation gap.
    """
    top_score = normalized_scores.get(top_branch, 0.0)
    # Weight: 70% absolute score, 30% gap separation
    confidence = (top_score * 0.7) + (min(gap_ratio, 1.0) * 0.3)
    return round(min(confidence, 1.0), 4)


def build_explanation(
    normalized_scores: dict[str, float],
    top_branch: str,
    is_tied: bool,
    second_branch: str,
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
        f"{top_branch} emerges as your strongest match ({normalized_scores[top_branch]:.0%}). "
        f"Full scores: [{score_lines}]"
    )


def evaluate(signals: dict[str, float]) -> ScoreResult:
    """
    Main entry: run full scoring pipeline.
    Returns a ScoreResult with all intermediate values for auditability.
    """
    raw = compute_branch_scores(signals)
    normalized = normalize_scores(raw)
    top_branch, second_branch, gap_ratio, is_tied = detect_tie(normalized)
    top_score = normalized.get(top_branch, 0.0)
    second_score = normalized.get(second_branch, 0.0)
    confidence = compute_confidence(normalized, top_branch, gap_ratio)
    explanation = build_explanation(normalized, top_branch, is_tied, second_branch)

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
    )
