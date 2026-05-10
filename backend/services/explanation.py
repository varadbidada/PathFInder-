"""
services/explanation.py — Human-Readable Output Generator
Builds the final counselling report from raw engine outputs.
"""
from __future__ import annotations
from models.college import CollegeRecommendation
from models.user_profile import UserProfile
from engines.rule_engine import ScoreResult


def format_fees(amount_inr: int) -> str:
    lakh = amount_inr / 100_000
    return f"₹{lakh:.1f}L/year"


def format_placement(amount_inr: int) -> str:
    lakh = amount_inr / 100_000
    if lakh >= 10:
        return f"₹{lakh / 10:.1f}Cr avg"
    return f"₹{lakh:.1f}L avg"


def build_branch_summary(result: ScoreResult) -> str:
    top = result.top_branch
    score = result.top_score
    conf = result.confidence

    quality = "very strong" if score > 0.8 else "strong" if score > 0.6 else "moderate"
    return (
        f"Your profile shows a **{quality} aptitude for {top} Engineering** "
        f"(score: {score:.0%}, confidence: {conf:.0%}). {result.explanation}"
    )


def build_counselling_report(
    profile: UserProfile,
    result: ScoreResult,
    recommendations: list[CollegeRecommendation],
) -> dict:
    """
    Build the full structured counselling report for the frontend.
    """
    grouped: dict[str, list[dict]] = {"Dream": [], "Moderate": [], "Safe": []}

    for college in recommendations:
        college_data = {
            "id": college.id,
            "name": college.name,
            "branch": college.branch,
            "location": college.location,
            "tier": college.recommendation_tier,
            "cutoff_rank": college.cutoff_rank,
            "annual_fees": format_fees(college.annual_fees),
            "annual_fees_raw": college.annual_fees,
            "placement_avg": format_placement(college.placement_avg),
            "placement_avg_raw": college.placement_avg,
            "accreditation": college.accreditation,
            "rank_gap": college.rank_gap,
            "reddit_insights": college.reddit_insights,
            "reddit_summary": college.reddit_summary,
        }
        grouped[college.recommendation_tier].append(college_data)

    return {
        "session_id": profile.session_id,
        "recommended_branch": result.top_branch,
        "branch_scores": result.normalized_scores,
        "confidence": result.confidence,
        "branch_summary": build_branch_summary(result),
        "student_rank": profile.rank,
        "budget_lakh": profile.budget_lakh,
        "preferred_location": profile.preferred_location,
        "is_tied": result.is_tied,
        "second_branch": result.second_branch if result.is_tied else None,
        "colleges": grouped,
        "total_colleges": len(recommendations),
    }


def build_profile_summary(profile: UserProfile, result: ScoreResult) -> str:
    """
    Build a human-readable summary of the student profile for the CONFIRMATION step.
    """
    lines = [
        "Here's what I've understood about you so far:",
        f"🎯 **Best-fit branch:** {result.top_branch} Engineering ({result.top_score:.0%} match)",
        f"📊 **JEE/State Rank:** {profile.rank or 'Not provided'}",
        f"💰 **Annual Budget:** {'₹' + str(profile.budget_lakh) + 'L' if profile.budget_lakh else 'Not specified'}",
        f"📍 **Location Preference:** {profile.preferred_location or 'Open to anywhere in India'}",
        f"🔍 **Confidence:** {result.confidence:.0%}",
    ]
    if result.is_tied:
        lines.append(
            f"⚡ **Note:** Your scores for {result.top_branch} and {result.second_branch} are very close!"
        )
    lines.append("\nDoes anything look incorrect? Reply to update, or type **'yes'** to get your college list!")
    return "\n".join(lines)
