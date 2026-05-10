"""
models/signals.py — AI Signal Extraction Schema
Strict Pydantic v2 validation for Claude's JSON output.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class SignalOutput(BaseModel):
    """
    The strict JSON contract returned by the AI signal extractor.
    All float fields must be clamped to [0.0, 1.0].
    """
    Logical_Thinking: float = Field(0.5, ge=0.0, le=1.0)
    Creativity: float = Field(0.5, ge=0.0, le=1.0)
    Manual_Work: float = Field(0.5, ge=0.0, le=1.0)
    Spatial_Awareness: float = Field(0.5, ge=0.0, le=1.0)
    Biology_Interest: float = Field(0.5, ge=0.0, le=1.0)
    Problem_Solving: float = Field(0.5, ge=0.0, le=1.0)
    Communication: float = Field(0.5, ge=0.0, le=1.0)
    Math_Aptitude: float = Field(0.5, ge=0.0, le=1.0)
    Risk_Level: Literal["low", "medium", "high"] = "medium"
    Suggested_Fields: list[str] = Field(default_factory=list)
    Confidence: float = Field(0.5, ge=0.0, le=1.0)

    @field_validator(
        "Logical_Thinking", "Creativity", "Manual_Work", "Spatial_Awareness",
        "Biology_Interest", "Problem_Solving", "Communication", "Math_Aptitude",
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
        """Return only the numeric signal fields (excludes Risk_Level, Suggested_Fields, Confidence)."""
        return {
            "Logical_Thinking": self.Logical_Thinking,
            "Creativity": self.Creativity,
            "Manual_Work": self.Manual_Work,
            "Spatial_Awareness": self.Spatial_Awareness,
            "Biology_Interest": self.Biology_Interest,
            "Problem_Solving": self.Problem_Solving,
            "Communication": self.Communication,
            "Math_Aptitude": self.Math_Aptitude,
        }


NEUTRAL_SIGNALS = SignalOutput()
