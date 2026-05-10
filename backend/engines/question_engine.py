"""
engines/question_engine.py — Dynamic Question Selector
Determines which question to ask next based on conversation state.
"""
from __future__ import annotations
import json
import os
from typing import Optional
from models.user_profile import UserProfile, QuestionCategory, CATEGORY_ORDER
from config import settings


_QUESTIONS: list[dict] | None = None


def _load_questions() -> list[dict]:
    global _QUESTIONS
    if _QUESTIONS is None:
        base = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base, settings.questions_file)
        with open(path, encoding="utf-8") as f:
            _QUESTIONS = json.load(f)
    return _QUESTIONS


def get_questions_for_category(category: str, follow_up: bool = False) -> list[dict]:
    """Return all main questions (or follow-up questions) for a category."""
    qs = _load_questions()
    return [q for q in qs if q["category"] == category and q.get("follow_up", False) == follow_up]


def select_next_question(profile: UserProfile) -> Optional[dict]:
    """
    Determine the next question to ask based on session state.
    Returns None if the conversation is complete.
    """
    if profile.is_complete:
        return None

    category = profile.current_category

    # Check if we've already asked a question from this category
    asked_ids = {m.content for m in profile.messages if m.role == "assistant"}
    candidates = get_questions_for_category(category, follow_up=False)

    # Filter to unasked questions
    unasked = [q for q in candidates if q["text"] not in asked_ids]

    if unasked:
        return unasked[0]

    # Advance to next category
    try:
        current_idx = CATEGORY_ORDER.index(category)  # type: ignore[arg-type]
    except ValueError:
        return None

    for next_category in CATEGORY_ORDER[current_idx + 1:]:
        # Skip TIE_BREAKER unless triggered
        if next_category == "TIE_BREAKER" and profile.tie_breaker_rounds == 0:
            continue
        next_qs = get_questions_for_category(next_category, follow_up=False)
        if next_qs:
            profile.current_category = next_category  # type: ignore[assignment]
            return next_qs[0]

    # All categories done → confirmation
    profile.current_category = "CONFIRMATION"  # type: ignore[assignment]
    conf_qs = get_questions_for_category("CONFIRMATION", follow_up=False)
    return conf_qs[0] if conf_qs else None


def advance_category(profile: UserProfile) -> None:
    """Move to the next question category in sequence."""
    try:
        idx = CATEGORY_ORDER.index(profile.current_category)  # type: ignore[arg-type]
    except ValueError:
        return
    if idx + 1 < len(CATEGORY_ORDER):
        profile.current_category = CATEGORY_ORDER[idx + 1]  # type: ignore[assignment]
    profile.categories_completed.append(profile.current_category)


def should_trigger_tie_breaker(profile: UserProfile, is_tied: bool) -> bool:
    """Return True if we should inject a TIE_BREAKER question next."""
    return (
        is_tied
        and profile.tie_breaker_rounds < settings.max_tie_breaker_rounds
        and "TIE_BREAKER" not in profile.categories_completed
    )
