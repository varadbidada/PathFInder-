"""
models/signals.py — AI Signal Extraction Schema
Strict Pydantic v2 validation for Claude's JSON output.

Enhanced with ability/enthusiasm split:
- Each dimension has TWO values: _ability (how good they are) and _enthusiasm (how much they enjoy it)
- Scoring formula: 0.4 * ability + 0.6 * enthusiasm (enthusiasm predicts long-term satisfaction)
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class SignalOutput(BaseModel):
    """
    The strict JSON contract returned by the AI signal extractor.
    All float fields must be clamped to [0.0, 1.0].
    
    Each core dimension is split into:
    - _ability: How skilled/capable the student is (0.0-1.0)
    - _enthusiasm: How much they enjoy/are passionate about it (0.0-1.0)
    """
    # Logical Thinking (coding, algorithms, abstract reasoning)
    Logical_Thinking_ability: float = Field(0.5, ge=0.0, le=1.0)
    Logical_Thinking_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Creativity (design, innovation, artistic thinking)
    Creativity_ability: float = Field(0.5, ge=0.0, le=1.0)
    Creativity_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Manual Work (hands-on, building, physical work)
    Manual_Work_ability: float = Field(0.5, ge=0.0, le=1.0)
    Manual_Work_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Spatial Awareness (3D visualization, geometry, architecture)
    Spatial_Awareness_ability: float = Field(0.5, ge=0.0, le=1.0)
    Spatial_Awareness_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Biology Interest (life sciences, medicine, healthcare)
    Biology_Interest_ability: float = Field(0.5, ge=0.0, le=1.0)
    Biology_Interest_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Problem Solving (analytical thinking, debugging, troubleshooting)
    Problem_Solving_ability: float = Field(0.5, ge=0.0, le=1.0)
    Problem_Solving_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Communication (teamwork, presentation, writing)
    Communication_ability: float = Field(0.5, ge=0.0, le=1.0)
    Communication_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Math Aptitude (calculus, algebra, quantitative reasoning)
    Math_Aptitude_ability: float = Field(0.5, ge=0.0, le=1.0)
    Math_Aptitude_enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    
    # Personality dimensions
    Introvert_Extrovert: Literal["introvert", "ambivert", "extrovert"] = "ambivert"
    Risk_Level: Literal["low", "medium", "high"] = "medium"
    
    # Exam information
    Exam_Type: Literal["jee_main", "jee_advanced", "unknown"] = "unknown"
    
    # Metadata
    Suggested_Fields: list[str] = Field(default_factory=list)
    Confidence: float = Field(0.5, ge=0.0, le=1.0)

    @field_validator(
        "Logical_Thinking_ability", "Logical_Thinking_enthusiasm",
        "Creativity_ability", "Creativity_enthusiasm",
        "Manual_Work_ability", "Manual_Work_enthusiasm",
        "Spatial_Awareness_ability", "Spatial_Awareness_enthusiasm",
        "Biology_Interest_ability", "Biology_Interest_enthusiasm",
        "Problem_Solving_ability", "Problem_Solving_enthusiasm",
        "Communication_ability", "Communication_enthusiasm",
        "Math_Aptitude_ability", "Math_Aptitude_enthusiasm",
        "Confidence", mode="before"
    )
    @classmethod
    def clamp_float(cls, v: object) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (TypeError, ValueError):
            return 0.5

    def to_dict(self) -> dict[str, float]:
        """
        Return all numeric signal fields as a flat dict.
        Includes both ability and enthusiasm for each dimension.
        """
        return {
            "Logical_Thinking_ability": self.Logical_Thinking_ability,
            "Logical_Thinking_enthusiasm": self.Logical_Thinking_enthusiasm,
            "Creativity_ability": self.Creativity_ability,
            "Creativity_enthusiasm": self.Creativity_enthusiasm,
            "Manual_Work_ability": self.Manual_Work_ability,
            "Manual_Work_enthusiasm": self.Manual_Work_enthusiasm,
            "Spatial_Awareness_ability": self.Spatial_Awareness_ability,
            "Spatial_Awareness_enthusiasm": self.Spatial_Awareness_enthusiasm,
            "Biology_Interest_ability": self.Biology_Interest_ability,
            "Biology_Interest_enthusiasm": self.Biology_Interest_enthusiasm,
            "Problem_Solving_ability": self.Problem_Solving_ability,
            "Problem_Solving_enthusiasm": self.Problem_Solving_enthusiasm,
            "Communication_ability": self.Communication_ability,
            "Communication_enthusiasm": self.Communication_enthusiasm,
            "Math_Aptitude_ability": self.Math_Aptitude_ability,
            "Math_Aptitude_enthusiasm": self.Math_Aptitude_enthusiasm,
        }
    
    def get_combined_score(self, dimension: str) -> float:
        """
        Compute combined score for a dimension: 0.4 * ability + 0.6 * enthusiasm.
        
        Args:
            dimension: Base dimension name (e.g., "Logical_Thinking")
        
        Returns:
            Combined score [0.0, 1.0]
        """
        ability = getattr(self, f"{dimension}_ability", 0.5)
        enthusiasm = getattr(self, f"{dimension}_enthusiasm", 0.5)
        return 0.4 * ability + 0.6 * enthusiasm
    
    def get_enthusiasm_gap(self, dimension: str) -> float:
        """
        Compute enthusiasm gap: ability - enthusiasm.
        Positive gap = high ability but low enthusiasm (warning sign).
        Negative gap = high enthusiasm but low ability (growth potential).
        
        Args:
            dimension: Base dimension name (e.g., "Logical_Thinking")
        
        Returns:
            Gap value [-1.0, 1.0]
        """
        ability = getattr(self, f"{dimension}_ability", 0.5)
        enthusiasm = getattr(self, f"{dimension}_enthusiasm", 0.5)
        return ability - enthusiasm


NEUTRAL_SIGNALS = SignalOutput()
