"""
services/explanation.py — Human-Readable Output Generator
Builds the final counselling report from raw engine outputs.

Enhanced with ability/enthusiasm breakdown:
- Shows which signals drove each branch recommendation
- Highlights enthusiasm vs ability gaps
- Provides "Watch out" warnings for high ability but low enthusiasm
"""
from __future__ import annotations
from models.college import CollegeRecommendation
from models.user_profile import UserProfile
from models.signals import SignalOutput
from engines.rule_engine import ScoreResult


def format_fees(amount_inr: int) -> str:
    lakh = amount_inr / 100_000
    return f"₹{lakh:.1f}L/year"


def format_placement(amount_inr: int) -> str:
    lakh = amount_inr / 100_000
    if lakh >= 10:
        return f"₹{lakh / 10:.1f}Cr avg"
    return f"₹{lakh:.1f}L avg"


def build_signal_explanation(branch: str, breakdown: dict[str, float], gaps: dict[str, float]) -> list[str]:
    """
    Build human-readable explanation of which signals drove a branch recommendation.
    
    Args:
        branch: Branch name
        breakdown: dict[dimension, contribution]
        gaps: dict[dimension, ability - enthusiasm]
    
    Returns:
        List of explanation strings
    """
    explanations = []
    
    # Sort by contribution (highest first)
    sorted_signals = sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)
    
    # Top 3 positive contributors
    positive_signals = [(dim, contrib) for dim, contrib in sorted_signals if contrib > 0.1][:3]
    
    if positive_signals:
        signal_names = []
        for dim, contrib in positive_signals:
            # Check for enthusiasm gap
            gap = gaps.get(dim, 0.0)
            if gap > 0.3:
                # High ability but low enthusiasm
                signal_names.append(f"{dim.replace('_', ' ')} (⚠️ ability > enthusiasm)")
            else:
                signal_names.append(dim.replace('_', ' '))
        
        explanations.append(f"✓ Strong in: {', '.join(signal_names)}")
    
    return explanations


def build_enthusiasm_warnings(branch: str, gaps: dict[str, float], signals: SignalOutput) -> list[str]:
    """
    Build warnings for dimensions where ability is high but enthusiasm is low.
    
    Args:
        branch: Branch name
        gaps: dict[dimension, ability - enthusiasm]
        signals: SignalOutput with ability/enthusiasm values
    
    Returns:
        List of warning strings
    """
    warnings = []
    
    # Check for significant gaps (ability > enthusiasm by 0.3+)
    for dimension, gap in gaps.items():
        if gap > 0.3:
            ability_key = f"{dimension}_ability"
            enthusiasm_key = f"{dimension}_enthusiasm"
            
            ability = getattr(signals, ability_key, 0.5)
            enthusiasm = getattr(signals, enthusiasm_key, 0.5)
            
            if ability > 0.6:  # Only warn if ability is actually high
                warnings.append(
                    f"⚠️ {dimension.replace('_', ' ')}: High ability ({ability:.0%}) but low enthusiasm ({enthusiasm:.0%}). "
                    f"Consider if you'd enjoy this long-term."
                )
    
    return warnings


def build_branch_summary(result: ScoreResult, signals: SignalOutput | None = None) -> str:
    """
    Build a summary of the branch recommendation with confidence label.
    
    Args:
        result: ScoreResult from rule engine
        signals: Optional SignalOutput for detailed breakdown
    
    Returns:
        Formatted summary string
    """
    top = result.top_branch
    score = result.top_score
    conf = result.confidence
    
    # Get confidence label from result (computed in rule_engine)
    conf_label = "Strong Match" if conf >= 0.75 else "Good Match" if conf >= 0.60 else "Moderate Match" if conf >= 0.40 else "Weak Match"
    
    if result.is_tied:
        return (
            f"**Tie Detected (Confidence: {conf:.0%})**\n"
            f"{result.explanation}"
        )
    
    summary_lines = [
        f"**{top} Engineering — {conf_label}** ({score:.0%} match, {conf:.0%} confidence)\n",
        result.explanation
    ]
    
    # Add signal breakdown if available
    if signals and top in result.signal_breakdown:
        breakdown = result.signal_breakdown[top]
        gaps = result.enthusiasm_gaps.get(top, {})
        
        signal_explanations = build_signal_explanation(top, breakdown, gaps)
        if signal_explanations:
            summary_lines.append("\n" + "\n".join(signal_explanations))
        
        # Add enthusiasm warnings
        warnings = build_enthusiasm_warnings(top, gaps, signals)
        if warnings:
            summary_lines.append("\n**Watch Out:**")
            summary_lines.extend(warnings)
    
    # Add penalties if any
    if top in result.penalties_applied and result.penalties_applied[top]:
        summary_lines.append("\n**Note:** Some requirements not fully met:")
        for penalty in result.penalties_applied[top][:2]:  # Show max 2 penalties
            summary_lines.append(f"  • {penalty}")
    
    return "\n".join(summary_lines)


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
        "option_entry_list": [
            {
                "id": c.id,
                "name": c.name,
                "branch": c.branch,
                "location": c.location,
                "tier": c.recommendation_tier
            }
            for c in recommendations
        ]
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
