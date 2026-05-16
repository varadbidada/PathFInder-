"""
services/novel_features.py — Novel Features for Pathfinder

Implements unique features that differentiate Pathfinder from generic counsellors:
- What-If Rank Simulator
- Peer Comparison Stats
- Placement Reality Check
- Branch-Career Roadmap
- Sentiment Dashboard for Parents
"""
from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

from groq import AsyncGroq
from config import settings
from engines.recommendation import recommend, _load_colleges
from models.college import College

logger = logging.getLogger(__name__)


# ── Feature 9A: What-If Rank Simulator ────────────────────────────────────────

async def simulate_rank_change(
    current_rank: int,
    target_rank: int,
    branch: str,
    location: Optional[str] = None,
    budget_lakh: Optional[float] = None,
    rank_type: str = "jee_main",
) -> dict:
    """
    Simulate what colleges a student gains/loses by improving their rank.
    
    Args:
        current_rank: Student's current rank
        target_rank: Hypothetical improved rank
        branch: Engineering branch
        location: Preferred location (optional)
        budget_lakh: Budget constraint (optional)
        rank_type: "jee_advanced" or "jee_main"
    
    Returns:
        {
            "colleges_gained": list[dict],
            "colleges_lost": list[dict],
            "rank_improvement_needed": int,
            "current_count": int,
            "target_count": int
        }
    """
    # Get recommendations for current rank
    current_colleges = recommend(
        student_rank=current_rank,
        branch=branch,
        budget_lakh=budget_lakh,
        preferred_location=location,
        rank_type=rank_type,
        max_results_per_tier=20  # Get more for comparison
    )
    
    # Get recommendations for target rank
    target_colleges = recommend(
        student_rank=target_rank,
        branch=branch,
        budget_lakh=budget_lakh,
        preferred_location=location,
        rank_type=rank_type,
        max_results_per_tier=20
    )
    
    # Convert to sets for comparison
    current_ids = {c.id for c in current_colleges}
    target_ids = {c.id for c in target_colleges}
    
    # Find gained and lost colleges
    gained_ids = target_ids - current_ids
    lost_ids = current_ids - target_ids
    
    # Build detailed lists
    colleges_gained = [
        {
            "id": c.id,
            "name": c.name,
            "branch": c.branch,
            "location": c.location,
            "tier": c.recommendation_tier,
            "cutoff_rank": c.cutoff_rank,
            "annual_fees": c.annual_fees,
            "placement_avg": c.placement_avg,
        }
        for c in target_colleges if c.id in gained_ids
    ]
    
    colleges_lost = [
        {
            "id": c.id,
            "name": c.name,
            "branch": c.branch,
            "location": c.location,
            "tier": c.recommendation_tier,
            "cutoff_rank": c.cutoff_rank,
            "annual_fees": c.annual_fees,
            "placement_avg": c.placement_avg,
        }
        for c in current_colleges if c.id in lost_ids
    ]
    
    return {
        "colleges_gained": colleges_gained,
        "colleges_lost": colleges_lost,
        "rank_improvement_needed": current_rank - target_rank,
        "current_count": len(current_colleges),
        "target_count": len(target_colleges),
    }


# ── Feature 9C: Placement Reality Check ───────────────────────────────────────

async def get_placement_reality(
    college_name: str,
    branch: str,
) -> dict:
    """
    Get realistic placement statistics using Groq.
    
    Asks for median vs headline salary distinction to avoid inflated marketing numbers.
    
    Args:
        college_name: College name
        branch: Engineering branch
    
    Returns:
        {
            "median_salary_lpa": float,
            "headline_salary_lpa": float,
            "placement_percentage": float,
            "inflation_ratio": float,
            "is_inflated": bool,
            "reality_note": str
        }
    """
    try:
        client = AsyncGroq(api_key=settings.groq_api_key)
        
        prompt = f"""For {college_name} {branch} Engineering, provide realistic placement statistics.

CRITICAL: Distinguish between MEDIAN salary (what most students get) and HEADLINE salary (highest package used in marketing).

Return ONLY a JSON object with these exact fields:
{{
  "median_salary_lpa": <float>,
  "headline_salary_lpa": <float>,
  "placement_percentage": <float 0-100>,
  "reality_note": "<one sentence honest assessment>"
}}

Rules:
- median_salary_lpa: Realistic salary for 50th percentile student (in LPA)
- headline_salary_lpa: Highest package reported (often inflated)
- placement_percentage: % of students who actually get placed (be honest)
- reality_note: One sentence about placement reality (avoid marketing speak)

Example for IIT Bombay CS:
{{
  "median_salary_lpa": 18.5,
  "headline_salary_lpa": 45.0,
  "placement_percentage": 95.0,
  "reality_note": "Strong placements with most students getting 15-20 LPA offers from top companies."
}}

Now analyze {college_name} {branch}:"""

        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=400,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        
        import json
        import re
        
        raw_text = response.choices[0].message.content
        
        # Extract JSON from response
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(raw_text)
        
        # Calculate inflation ratio
        median = data.get("median_salary_lpa", 0)
        headline = data.get("headline_salary_lpa", 0)
        
        inflation_ratio = headline / median if median > 0 else 1.0
        is_inflated = inflation_ratio > 3.0  # Flag if headline is 3x+ median
        
        return {
            "median_salary_lpa": median,
            "headline_salary_lpa": headline,
            "placement_percentage": data.get("placement_percentage", 0),
            "inflation_ratio": round(inflation_ratio, 2),
            "is_inflated": is_inflated,
            "reality_note": data.get("reality_note", ""),
        }
        
    except Exception as e:
        logger.error(f"Placement reality check failed for {college_name} {branch}: {e}")
        return {
            "median_salary_lpa": 0,
            "headline_salary_lpa": 0,
            "placement_percentage": 0,
            "inflation_ratio": 1.0,
            "is_inflated": False,
            "reality_note": "Placement data unavailable",
        }


# ── Feature 9D: Branch-Career Roadmap ─────────────────────────────────────────

async def generate_career_roadmap(
    branch: str,
    college_tier: str = "Moderate",
) -> dict:
    """
    Generate a realistic 5-year career roadmap using Groq.
    
    Args:
        branch: Engineering branch
        college_tier: "Dream" | "Moderate" | "Safe"
    
    Returns:
        {
            "year_1": {"title": str, "description": str},
            "year_2_3": {"title": str, "description": str},
            "year_4": {"title": str, "description": str},
            "year_5": {"title": str, "description": str}
        }
    """
    try:
        client = AsyncGroq(api_key=settings.groq_api_key)
        
        prompt = f"""Generate a realistic 5-year career roadmap for a {branch} Engineering student from a {college_tier}-tier college.

Return ONLY a JSON object with these exact fields:
{{
  "year_1": {{
    "title": "<short title>",
    "description": "<2-3 sentences about internships to target, skills to build>"
  }},
  "year_2_3": {{
    "title": "<short title>",
    "description": "<2-3 sentences about skill development, projects, competitions>"
  }},
  "year_4": {{
    "title": "<short title>",
    "description": "<2-3 sentences about placement prep, resume building>"
  }},
  "year_5": {{
    "title": "<short title>",
    "description": "<2-3 sentences about first job reality, salary expectations>"
  }}
}}

Rules:
- Be REALISTIC, not aspirational
- Adjust expectations based on college tier ({college_tier})
- Include specific company names, salary ranges, skill requirements
- Mention challenges and common pitfalls
- Keep each description under 100 words

Example for CS from Moderate-tier college:
{{
  "year_1": {{
    "title": "Foundation & First Internship",
    "description": "Focus on DSA, web development basics. Target local startups or small companies for summer internship (₹10-15k/month). Build 2-3 projects for GitHub. Join coding clubs."
  }},
  "year_2_3": {{
    "title": "Skill Building & Competitions",
    "description": "Master one tech stack (MERN/Django). Participate in hackathons. Aim for better internship at mid-size companies (₹25-40k/month). Contribute to open source. Build portfolio."
  }},
  "year_4": {{
    "title": "Placement Preparation",
    "description": "Grind LeetCode (300+ problems). Practice system design. Target service-based companies (TCS, Infosys: ₹3.5-4.5 LPA) and product companies (₹6-12 LPA). Prepare for off-campus opportunities."
  }},
  "year_5": {{
    "title": "First Job Reality",
    "description": "Expect ₹4-8 LPA for most placements. Service companies offer stability but slower growth. Product companies offer better learning. Focus on skill development over salary in first 2 years. Plan for job switch after 1.5-2 years for 50-80% hike."
  }}
}}

Now generate roadmap for {branch} from {college_tier}-tier college:"""

        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=800,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}],
        )
        
        import json
        import re
        
        raw_text = response.choices[0].message.content
        
        # Extract JSON from response
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(raw_text)
        
        return data
        
    except Exception as e:
        logger.error(f"Career roadmap generation failed for {branch}: {e}")
        return {
            "year_1": {
                "title": "Foundation Year",
                "description": "Focus on building strong fundamentals and exploring different areas."
            },
            "year_2_3": {
                "title": "Skill Development",
                "description": "Develop specialized skills and gain practical experience through internships."
            },
            "year_4": {
                "title": "Placement Preparation",
                "description": "Prepare for campus placements and build a strong resume."
            },
            "year_5": {
                "title": "Career Start",
                "description": "Begin your professional career and continue learning on the job."
            }
        }


# ── Feature 9E: Generate PDF Report ───────────────────────────────────────────

def generate_parent_report(
    session_id: str,
    student_name: str,
    branch_recommendation: str,
    confidence: float,
    top_colleges: list[dict],
    reddit_summary: list[str],
    twitter_summary: list[str],
    placement_stats: dict,
) -> dict:
    """
    Generate a structured report for parents.
    
    Note: Actual PDF generation would require reportlab or similar.
    This returns structured data that can be rendered as PDF by frontend.
    
    Args:
        session_id: Session identifier
        student_name: Student's name
        branch_recommendation: Recommended branch
        confidence: Confidence score
        top_colleges: Top 3 recommended colleges
        reddit_summary: Reddit insights
        twitter_summary: Twitter insights
        placement_stats: Placement statistics
    
    Returns:
        Structured report data
    """
    report = {
        "report_id": f"PATHFINDER_{session_id[:8].upper()}",
        "generated_at": datetime.utcnow().isoformat(),
        "student_name": student_name,
        "summary": {
            "recommended_branch": branch_recommendation,
            "confidence": f"{confidence:.0%}",
            "confidence_label": "High" if confidence >= 0.75 else "Moderate" if confidence >= 0.60 else "Low",
        },
        "top_colleges": top_colleges[:3],
        "social_proof": {
            "reddit_insights": reddit_summary,
            "twitter_insights": twitter_summary,
        },
        "placement_reality": placement_stats,
        "disclaimer": (
            "This report is generated by Pathfinder AI based on the student's responses "
            "during the counselling session. Recommendations are data-driven but should be "
            "verified with official college websites and placement reports. Social media "
            "insights are aggregated from public sources and may not represent all student experiences."
        ),
    }
    
    return report
