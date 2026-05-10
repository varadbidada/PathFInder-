"""
engines/recommendation.py — College Tier Classifier
Classifies colleges into Dream / Moderate / Safe tiers based on student rank.
"""
from __future__ import annotations
import json
import os
from typing import Optional
from models.college import College, CollegeRecommendation, RecommendationTier
from config import settings


_COLLEGES: list[College] | None = None


def _load_colleges() -> list[College]:
    global _COLLEGES
    if _COLLEGES is None:
        base = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base, settings.colleges_file)
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        _COLLEGES = [College(**c) for c in raw]
    return _COLLEGES


def _classify_tier(student_rank: int, cutoff_rank: int) -> RecommendationTier:
    """
    Classify a college relative to a student's rank.

    Lower rank number = better rank (rank 1 is the best).
    cutoff_rank < student_rank means the college is hard to get → Dream.
    cutoff_rank > student_rank means students rank is better than cutoff → Safe.

    Dream:    cutoff is better (lower) than student rank by > dream_rank_gap
    Safe:     student rank is better (lower) than cutoff by > moderate_rank_gap
    Moderate: everything in between
    """
    gap = cutoff_rank - student_rank  # positive = college is easier (safer)

    if gap < -settings.dream_rank_gap:
        return "Dream"
    elif gap > settings.moderate_rank_gap:
        return "Safe"
    else:
        return "Moderate"


def recommend(
    student_rank: int,
    branch: str,
    budget_lakh: Optional[float] = None,
    preferred_location: Optional[str] = None,
    max_results_per_tier: int = 5,
) -> list[CollegeRecommendation]:
    """
    Return ranked college recommendations for a student.

    Filters by:
    - Branch match
    - Budget (if provided)
    - Location preference (if provided)

    Sorted within each tier by: placement_avg DESC, annual_fees ASC
    """
    colleges = _load_colleges()

    # Filter by branch
    branch_colleges = [c for c in colleges if c.branch.lower() == branch.lower()]

    # Filter by budget
    if budget_lakh is not None:
        branch_colleges = [
            c for c in branch_colleges if c.annual_fees / 100_000 <= budget_lakh
        ]

    # Filter by location preference (partial match, case-insensitive)
    if preferred_location:
        loc_lower = preferred_location.lower()
        location_filtered = [
            c for c in branch_colleges
            if loc_lower in c.location.lower() or c.location.lower() in loc_lower
        ]
        # Fall back to all if filter is too restrictive
        if location_filtered:
            branch_colleges = location_filtered

    recommendations: list[CollegeRecommendation] = []
    for college in branch_colleges:
        tier = _classify_tier(student_rank, college.cutoff_rank)
        rank_gap = college.cutoff_rank - student_rank
        rec = CollegeRecommendation(
            **college.model_dump(),
            recommendation_tier=tier,
            rank_gap=rank_gap,
        )
        recommendations.append(rec)

    # Sort within tiers: placement DESC, fees ASC
    def sort_key(r: CollegeRecommendation) -> tuple:
        tier_order = {"Dream": 0, "Moderate": 1, "Safe": 2}
        return (tier_order[r.recommendation_tier], -r.placement_avg, r.annual_fees)

    recommendations.sort(key=sort_key)

    # Cap per tier
    result: list[CollegeRecommendation] = []
    tier_counts: dict[str, int] = {"Dream": 0, "Moderate": 0, "Safe": 0}
    for rec in recommendations:
        t = rec.recommendation_tier
        if tier_counts[t] < max_results_per_tier:
            result.append(rec)
            tier_counts[t] += 1

    return result


def get_available_branches() -> list[str]:
    colleges = _load_colleges()
    return sorted(set(c.branch for c in colleges))
