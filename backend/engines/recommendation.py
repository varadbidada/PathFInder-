"""
engines/recommendation.py — College Tier Classifier
Classifies colleges into Dream / Moderate / Safe tiers based on student rank.
Integrates ML predictions for 2025 cutoffs when available.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Optional, Dict, Tuple
from models.college import College, CollegeRecommendation, RecommendationTier
from config import settings

logger = logging.getLogger(__name__)


_COLLEGES: list[College] | None = None
_PREDICTIONS: Dict[Tuple[str, str, str, str], Dict] | None = None


def _load_predictions() -> Dict[Tuple[str, str, str, str], Dict]:
    """Load ML predictions for 2025 cutoffs"""
    global _PREDICTIONS
    if _PREDICTIONS is None:
        base = os.path.dirname(os.path.dirname(__file__))
        pred_path = os.path.join(base, "data", "cutoff_predictions_2025.json")
        
        if os.path.exists(pred_path):
            with open(pred_path, encoding="utf-8") as f:
                predictions_list = json.load(f)
            
            # Build lookup dict keyed by (institute, branch, category, gender)
            _PREDICTIONS = {}
            for pred in predictions_list:
                key = (
                    pred['institute'],
                    pred['branch'],
                    pred['category'],
                    pred['gender']
                )
                _PREDICTIONS[key] = pred
            
            logger.info(f"Loaded {len(_PREDICTIONS)} ML predictions for 2025 cutoffs")
        else:
            _PREDICTIONS = {}
            logger.info("No ML predictions found, using historical data only")
    
    return _PREDICTIONS


def _load_colleges() -> list[College]:
    global _COLLEGES
    if _COLLEGES is None:
        base = os.path.dirname(os.path.dirname(__file__))
        
        # Try JoSAA database first (real data), fall back to old colleges.json
        josaa_path = os.path.join(base, "data", "colleges_josaa.json")
        fallback_path = os.path.join(base, settings.colleges_file)
        
        if os.path.exists(josaa_path):
            path = josaa_path
            logger.info("Loading JoSAA college database (real cutoff data)")
        else:
            path = fallback_path
            logger.warning(f"JoSAA database not found, using fallback: {fallback_path}")
        
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        _COLLEGES = [College(**c) for c in raw]
    return _COLLEGES


def _get_cutoff_with_prediction(college: College) -> Tuple[int, str, bool]:
    """
    Get the cutoff rank for a college, using ML prediction if available.
    
    Returns:
        (cutoff_rank, source, low_confidence)
    """
    predictions = _load_predictions()
    
    # Branch name mapping for better matching
    branch_mapping = {
        "CS": ["computer science", "computer", "cse"],
        "Electronics": ["electronics", "ece", "electrical", "communication"],
        "Mechanical": ["mechanical", "mech"],
        "Civil": ["civil"],
        "Medical": ["medical", "biomedical", "biotechnology"]
    }
    
    # Get possible branch names for this college's branch
    possible_branches = branch_mapping.get(college.branch, [college.branch.lower()])
    
    # Try to find ML prediction
    for (inst, branch, category, gender), pred in predictions.items():
        # Institute name matching (more flexible)
        inst_match = (
            inst.lower() in college.name.lower() or 
            college.name.lower() in inst.lower() or
            # Handle "IIT" matching
            ("iit" in inst.lower() and "iit" in college.name.lower() and 
             any(word in inst.lower() for word in college.name.lower().split()))
        )
        
        # Branch matching (check if any possible branch name is in the prediction branch)
        branch_match = any(pb in branch.lower() for pb in possible_branches)
        
        if inst_match and branch_match:
            # Found a match - prefer OPEN category and Gender-Neutral
            if category == "OPEN" and gender == "Gender-Neutral":
                if pred['low_confidence']:
                    # Average predicted and actual 2024
                    cutoff = int((pred['predicted_closing_rank_2025'] + pred['actual_closing_rank_2024']) / 2)
                    return cutoff, "ml_prediction_2025_low_conf", True
                else:
                    return pred['predicted_closing_rank_2025'], "ml_prediction_2025", False
    
    # Second pass: try any category/gender if OPEN/Gender-Neutral not found
    for (inst, branch, category, gender), pred in predictions.items():
        inst_match = (
            inst.lower() in college.name.lower() or 
            college.name.lower() in inst.lower() or
            ("iit" in inst.lower() and "iit" in college.name.lower() and 
             any(word in inst.lower() for word in college.name.lower().split()))
        )
        
        branch_match = any(pb in branch.lower() for pb in possible_branches)
        
        if inst_match and branch_match:
            if pred['low_confidence']:
                cutoff = int((pred['predicted_closing_rank_2025'] + pred['actual_closing_rank_2024']) / 2)
                return cutoff, "ml_prediction_2025_low_conf", True
            else:
                return pred['predicted_closing_rank_2025'], "ml_prediction_2025", False
    
    # No prediction found, use historical
    return college.cutoff_rank, "historical_average", False


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
    rank_type: str = "jee_main",  # "jee_advanced" or "jee_main"
    max_results_per_tier: int = 5,
) -> list[CollegeRecommendation]:
    """
    Return ranked college recommendations for a student.

    Filters by:
    - Branch match
    - Rank type (JEE Advanced vs JEE Main) — CRITICAL: never compare across types
    - Budget (if provided)
    - Location preference (if provided)

    Sorted within each tier by: placement_avg DESC, annual_fees ASC
    """
    colleges = _load_colleges()

    # Filter by branch
    branch_colleges = [c for c in colleges if c.branch.lower() == branch.lower()]

    # CRITICAL: Filter by rank type to avoid comparing JEE Advanced ranks with JEE Main cutoffs
    branch_colleges = [c for c in branch_colleges if c.rank_type == rank_type]

    # Filter by budget
    if budget_lakh is not None:
        branch_colleges = [
            c for c in branch_colleges if c.annual_fees / 100_000 <= budget_lakh
        ]

    # Filter by location preference
    unfiltered_branch_colleges = list(branch_colleges)
    if preferred_location:
        loc_lower = preferred_location.lower()
        
        # Smart mapping for common cities to states
        city_to_state = {
            "bengaluru": "karnataka", "bangalore": "karnataka",
            "mumbai": "maharashtra", "pune": "maharashtra", "nagpur": "maharashtra",
            "chennai": "tamil nadu", "trichy": "tamil nadu", "vellore": "tamil nadu",
            "hyderabad": "telangana", "warangal": "telangana",
            "jaipur": "rajasthan", "pilani": "rajasthan", "kota": "rajasthan",
            "lucknow": "uttar pradesh", "kanpur": "uttar pradesh", "noida": "uttar pradesh",
            "delhi": "delhi", "new delhi": "delhi",
            "kolkata": "west bengal", "kharagpur": "west bengal"
        }
        
        mapped_state = city_to_state.get(loc_lower, loc_lower)
        
        location_filtered = [
            c for c in branch_colleges
            if loc_lower in c.location.lower() or c.location.lower() in loc_lower
            or mapped_state in c.location.lower()
            or loc_lower in c.name.lower()
        ]
        
        # If the location is too restrictive (0 matches), fall back to all colleges
        if location_filtered:
            branch_colleges = location_filtered

    # Primary pass: Colleges that match the location
    recommendations: list[CollegeRecommendation] = []
    seen_ids = set()
    for college in branch_colleges:
        # Get cutoff with ML prediction if available
        cutoff_rank, cutoff_source, low_confidence = _get_cutoff_with_prediction(college)
        
        tier = _classify_tier(student_rank, cutoff_rank)
        rank_gap = cutoff_rank - student_rank
        rec = CollegeRecommendation(
            **college.model_dump(),
            recommendation_tier=tier,
            rank_gap=rank_gap,
            cutoff_source=cutoff_source,
            low_confidence=low_confidence,
        )
        recommendations.append(rec)
        seen_ids.add(college.id)

    # Sort within tiers
    def sort_key(r: CollegeRecommendation) -> tuple:
        tier_order = {"Dream": 0, "Moderate": 1, "Safe": 2}
        
        # For Dream: simply show the absolute best colleges (highest placement)
        if r.recommendation_tier == "Dream":
            return (tier_order[r.recommendation_tier], -r.placement_avg, r.annual_fees)
        
        # For Moderate: show colleges where the cutoff is closest to their rank
        elif r.recommendation_tier == "Moderate":
            return (tier_order[r.recommendation_tier], abs(r.rank_gap), -r.placement_avg)
        
        # For Safe: show the "best" safe colleges (rank gap is positive, but as small as possible)
        else:
            return (tier_order[r.recommendation_tier], r.rank_gap, -r.placement_avg)

    recommendations.sort(key=sort_key)

    # Cap per tier
    result: list[CollegeRecommendation] = []
    tier_counts: dict[str, int] = {"Dream": 0, "Moderate": 0, "Safe": 0}
    for rec in recommendations:
        t = rec.recommendation_tier
        if tier_counts[t] < max_results_per_tier:
            result.append(rec)
            tier_counts[t] += 1
            
    # Backfill with unfiltered colleges if we don't have enough
    total_recs = sum(tier_counts.values())
    if preferred_location and total_recs < (max_results_per_tier * 3):
        backfill_recs = []
        for college in unfiltered_branch_colleges:
            if college.id not in seen_ids:
                cutoff_rank, cutoff_source, low_confidence = _get_cutoff_with_prediction(college)
                tier = _classify_tier(student_rank, cutoff_rank)
                rank_gap = cutoff_rank - student_rank
                rec = CollegeRecommendation(
                    **college.model_dump(),
                    recommendation_tier=tier,
                    rank_gap=rank_gap,
                    cutoff_source=cutoff_source,
                    low_confidence=low_confidence,
                )
                backfill_recs.append(rec)
        
        backfill_recs.sort(key=sort_key)
        
        for rec in backfill_recs:
            t = rec.recommendation_tier
            if tier_counts[t] < max_results_per_tier:
                # Add an indicator that it's a backfilled (nearby) college
                rec.name = f"{rec.name} (Other Region)"
                result.append(rec)
                tier_counts[t] += 1
                seen_ids.add(rec.id)

    # Final sort of the combined result list to group by tier
    result.sort(key=sort_key)

    return result


def get_available_branches() -> list[str]:
    colleges = _load_colleges()
    return sorted(set(c.branch for c in colleges))


def validate_cutoffs() -> None:
    """
    Validate cutoff ranks and log warnings for suspicious data.
    Call this on startup or after loading the database.
    """
    colleges = _load_colleges()
    warnings = []
    
    for college in colleges:
        rank = college.cutoff_rank
        name = college.name
        branch = college.branch
        rank_type = college.rank_type
        
        if rank_type == "jee_advanced":
            if rank < 50:
                warnings.append(f"Suspiciously low rank: {name} {branch} = {rank} (JEE Advanced)")
            elif rank > 20000:
                warnings.append(f"Suspiciously high rank: {name} {branch} = {rank} (JEE Advanced)")
        else:  # jee_main
            if rank < 100:
                warnings.append(f"Suspiciously low rank: {name} {branch} = {rank} (JEE Main)")
            elif rank > 500000:
                warnings.append(f"Suspiciously high rank: {name} {branch} = {rank} (JEE Main)")
    
    if warnings:
        logger.warning(f"Found {len(warnings)} suspicious cutoff ranks:")
        for w in warnings[:10]:  # Log first 10
            logger.warning(f"  {w}")
    else:
        logger.info("All cutoff ranks validated successfully.")
