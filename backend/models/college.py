"""
models/college.py — College Dataset Model
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


CollegeTier = Literal["elite", "premium", "good", "average"]
RecommendationTier = Literal["Dream", "Moderate", "Safe"]


class College(BaseModel):
    id: str
    name: str
    branch: str
    cutoff_rank: int
    rank_type: str = "jee_main"  # "jee_advanced" for IITs, "jee_main" for NITs/IIITs/GFTIs
    annual_fees: int  # in INR
    location: str
    tier: CollegeTier
    placement_avg: int  # in INR
    accreditation: str
    established: Optional[int] = None

    @property
    def fees_lakh(self) -> float:
        return round(self.annual_fees / 100_000, 1)

    @property
    def placement_lpa(self) -> float:
        return round(self.placement_avg / 100_000, 1)


class CollegeRecommendation(College):
    """
    A College with an assigned recommendation tier and optional Reddit insights.
    """
    recommendation_tier: RecommendationTier
    reddit_insights: list[str] = Field(default_factory=list)
    reddit_summary: Optional[str] = None
    rank_gap: int = 0  # positive = student rank is better (safer), negative = riskier
    cutoff_source: str = "historical_average"  # "ml_prediction_2025" or "historical_average"
    low_confidence: bool = False  # True if ML prediction has high uncertainty
