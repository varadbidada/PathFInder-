"""
models/user_profile.py — Session & User Profile Model
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


QuestionCategory = Literal[
    "INTEREST", "APTITUDE", "RANK", "BUDGET", "LOCATION", "TIE_BREAKER", "CONFIRMATION"
]

CATEGORY_ORDER: list[QuestionCategory] = [
    "INTEREST", "APTITUDE", "RANK", "BUDGET", "LOCATION", "TIE_BREAKER", "CONFIRMATION"
]


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BranchScores(BaseModel):
    CS: float = 0.0
    Electronics: float = 0.0
    Mechanical: float = 0.0
    Civil: float = 0.0
    Medical: float = 0.0


class UserProfile(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Conversation state
    messages: list[Message] = Field(default_factory=list)
    current_category: QuestionCategory = "INTEREST"
    categories_completed: list[str] = Field(default_factory=list)
    asked_question_ids: list[str] = Field(default_factory=list)
    tie_breaker_rounds: int = 0
    is_complete: bool = False

    # Extracted data
    rank: Optional[int] = None
    budget_lakh: Optional[float] = None  # Annual budget in lakhs
    preferred_location: Optional[str] = None
    branch_scores: BranchScores = Field(default_factory=BranchScores)
    cumulative_signals: dict[str, float] = Field(default_factory=dict)
    overall_confidence: float = 0.0
    recommended_branch: Optional[str] = None
    risk_level: Literal["low", "medium", "high"] = "medium"

    def add_message(self, role: Literal["user", "assistant", "system"], content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.utcnow()

    def get_conversation_text(self, last_n: int = 6) -> str:
        """Return recent conversation history as a formatted string for AI context."""
        recent = self.messages[-last_n:] if len(self.messages) > last_n else self.messages
        return "\n".join(f"{m.role.upper()}: {m.content}" for m in recent)
