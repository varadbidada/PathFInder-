"""
backend/main.py — FastAPI Application Entry Point
Production-grade: async, rate-limited, CORS-configured, structured logging.
"""
from __future__ import annotations
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import re

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from models.user_profile import UserProfile
from models.signals import SignalOutput
from engines.rule_engine import evaluate
from engines.recommendation import recommend, get_available_branches
from engines.question_engine import (
    select_next_question,
    should_trigger_tie_breaker,
    get_questions_for_category,
)
from services.ai_service import (
    extract_signals,
    generate_counsellor_response,
    summarize_reddit_insights,
    generate_tie_breaker_question,
)
from services.reddit_service import fetch_college_insights
from services.explanation import build_counselling_report, build_profile_summary


# ── Structured JSON Logging ───────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=settings.log_level, handlers=[handler])
logger = logging.getLogger("pathfinder")


# ── In-memory session store (replace with Redis in production) ────────────────
sessions: dict[str, UserProfile] = {}


# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pathfinder API starting up")
    yield
    logger.info("Pathfinder API shutting down")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Pathfinder AI Career Counsellor",
    description="Production-grade AI counselling API for Indian engineering students",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Input Sanitization ────────────────────────────────────────────────────────
def sanitize_input(text: str, max_len: int = 2000) -> str:
    text = text.strip()[:max_len]
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


# ── Request / Response Schemas ────────────────────────────────────────────────
class StartSessionResponse(BaseModel):
    session_id: str
    first_question: str
    message: str


class ChatRequest(BaseModel):
    session_id: str
    user_message: str = Field(..., max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    next_question: Optional[str]
    branch_scores: dict[str, float]
    overall_confidence: float
    current_category: str
    is_complete: bool
    profile_summary: Optional[str] = None
    report: Optional[dict] = None


class WhatIfRequest(BaseModel):
    session_id: str
    hypothetical_rank: int = Field(..., ge=1, le=1_000_000)


class CompareRequest(BaseModel):
    college_id_a: str
    college_id_b: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_session(session_id: str) -> UserProfile:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Please start a new session.")
    return sessions[session_id]


def _update_cumulative_signals(profile: UserProfile, new_signals: SignalOutput) -> None:
    """Merge new signals into cumulative profile using exponential moving average."""
    alpha = 0.4  # weight for new signals
    current = profile.cumulative_signals
    new_dict = new_signals.to_dict()
    for key, new_val in new_dict.items():
        old_val = current.get(key, settings.neutral_signal_default)
        current[key] = round(old_val * (1 - alpha) + new_val * alpha, 4)
    profile.overall_confidence = round(
        profile.overall_confidence * (1 - alpha) + new_signals.Confidence * alpha, 4
    )


def _update_branch_scores(profile: UserProfile, result) -> None:
    profile.branch_scores.CS = result.normalized_scores.get("CS", 0.0)
    profile.branch_scores.Electronics = result.normalized_scores.get("Electronics", 0.0)
    profile.branch_scores.Mechanical = result.normalized_scores.get("Mechanical", 0.0)
    profile.branch_scores.Civil = result.normalized_scores.get("Civil", 0.0)
    profile.branch_scores.Medical = result.normalized_scores.get("Medical", 0.0)


def _extract_rank(text: str) -> Optional[int]:
    """Try to parse a rank number from user text."""
    match = re.search(r'\b(\d{1,6})\b', text)
    if match:
        val = int(match.group(1))
        if 1 <= val <= 999_999:
            return val
    return None


def _extract_budget(text: str) -> Optional[float]:
    """Parse budget in lakh from user text."""
    text_lower = text.lower()
    if "2l" in text_lower or "2 l" in text_lower or "under 2" in text_lower or "2 lakh" in text_lower:
        return 2.0
    if "5l" in text_lower or "5 l" in text_lower or "5 lakh" in text_lower:
        return 5.0
    if "10" in text_lower or "above 5" in text_lower or "10+" in text_lower:
        return 15.0
    match = re.search(r'(\d+)\s*(?:lakh|l\b|lac)', text_lower)
    if match:
        return float(match.group(1))
    return None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "active_sessions": len(sessions),
    }


@app.post("/session/start", response_model=StartSessionResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def start_session(request: Request):
    """Create a new counselling session and return the first question."""
    # Parse optional form data from InitialForm
    try:
        body = await request.json()
    except Exception:
        body = {}

    profile = UserProfile()

    # Pre-populate profile from InitialForm data
    rank = body.get("jee_rank") or body.get("kcet_rank") or body.get("neet_rank")
    if rank is not None:
        try:
            profile.rank = int(rank)
            profile.categories_completed.append("RANK")
        except (ValueError, TypeError):
            pass

    budget = body.get("budget_lakh")
    if budget is not None:
        try:
            profile.budget_lakh = float(budget)
            profile.categories_completed.append("BUDGET")
        except (ValueError, TypeError):
            pass

    location = body.get("preferred_location")
    if location and str(location).strip():
        profile.preferred_location = str(location).strip()
        profile.categories_completed.append("LOCATION")

    sessions[profile.session_id] = profile

    first_q = select_next_question(profile)
    first_question_text = first_q["text"] if first_q else "Tell me about yourself!"

    skipped = len(profile.categories_completed)
    welcome = (
        "👋 Hi! I'm Pathfinder, your AI career counsellor. "
        + (f"Thanks for sharing your details upfront — I've saved your {'rank, ' if profile.rank else ''}{'budget, ' if profile.budget_lakh else ''}{'location ' if profile.preferred_location else ''}info. " if skipped > 0 else "")
        + "I'll ask you a few questions to figure out the best engineering branch and colleges for you. Let's start!"
    )
    profile.add_message("assistant", welcome)
    profile.add_message("assistant", first_question_text)

    logger.info({"event": "session_start", "session_id": profile.session_id, "prefilled": profile.categories_completed})
    return StartSessionResponse(
        session_id=profile.session_id,
        first_question=first_question_text,
        message=welcome,
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat(request: Request, body: ChatRequest):
    """Process a user message and return the next counsellor response."""
    profile = _get_session(body.session_id)
    user_text = sanitize_input(body.user_message)

    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    profile.add_message("user", user_text)

    # ── Extract contextual data from ANY message ──────────────────────────
    # Rank and budget are extracted regardless of current category so that
    # info-dense messages like "rank 45000, budget 5L" are captured early.
    category = profile.current_category

    if profile.rank is None:
        rank = _extract_rank(user_text)
        if rank:
            profile.rank = rank
            if "RANK" not in profile.categories_completed:
                profile.categories_completed.append("RANK")

    if profile.budget_lakh is None:
        budget = _extract_budget(user_text)
        if budget:
            profile.budget_lakh = budget
            if "BUDGET" not in profile.categories_completed:
                profile.categories_completed.append("BUDGET")

    if category == "LOCATION" and not profile.preferred_location:
        words = [w for w in user_text.split() if len(w) > 3]
        if words:
            profile.preferred_location = words[0].title()
            if "LOCATION" not in profile.categories_completed:
                profile.categories_completed.append("LOCATION")

    forced_override = False
    if category == "CONFIRMATION":
        text_lower = user_text.lower()
        if any(w in text_lower for w in ["cs", "computer", "cse"]):
            profile.cumulative_signals = {"Logical_Thinking": 1.0, "Math_Aptitude": 1.0, "Problem_Solving": 1.0}
            forced_override = True
        elif any(w in text_lower for w in ["electronic", "ece", "eee"]):
            profile.cumulative_signals = {"Math_Aptitude": 1.0, "Manual_Work": 1.0}
            forced_override = True
        elif any(w in text_lower for w in ["mechanic", "mech"]):
            profile.cumulative_signals = {"Manual_Work": 1.0, "Spatial_Awareness": 1.0}
            forced_override = True
        elif "civil" in text_lower:
            profile.cumulative_signals = {"Spatial_Awareness": 1.0, "Creativity": 1.0}
            forced_override = True
        elif any(w in text_lower for w in ["medic", "doctor", "mbbs"]):
            profile.cumulative_signals = {"Biology_Interest": 1.0}
            forced_override = True

    # ── Extract AI signals ────────────────────────────────────────────────
    last_assistant = next(
        (m.content for m in reversed(profile.messages) if m.role == "assistant"), ""
    )
    signals: SignalOutput = await extract_signals(
        user_answer=user_text,
        question_asked=last_assistant,
        conversation_context=profile.get_conversation_text(last_n=4),
    )
    _update_cumulative_signals(profile, signals)

    # ── Run Rule Engine ───────────────────────────────────────────────────
    result = evaluate(profile.cumulative_signals or signals.to_dict())
    _update_branch_scores(profile, result)
    profile.recommended_branch = result.top_branch
    profile.risk_level = signals.Risk_Level  # type: ignore[assignment]

    # ── Check for tie-breaker ─────────────────────────────────────────────
    if should_trigger_tie_breaker(profile, result.is_tied):
        tie_q = await generate_tie_breaker_question(result.top_branch, result.second_branch)
        profile.current_category = "TIE_BREAKER"  # type: ignore[assignment]
        profile.tie_breaker_rounds += 1
        profile.add_message("assistant", tie_q)
        return ChatResponse(
            session_id=profile.session_id,
            assistant_message=tie_q,
            next_question=tie_q,
            branch_scores=result.normalized_scores,
            overall_confidence=profile.overall_confidence,
            current_category="TIE_BREAKER",
            is_complete=False,
        )

    # ── Check if confirmation / completion ────────────────────────────────
    is_confirmation = profile.current_category == "CONFIRMATION"
    user_confirmed = any(
        word in user_text.lower()
        for word in ["yes", "correct", "proceed", "ok", "sure", "go ahead", "confirm"]
    )

    if is_confirmation and user_confirmed and profile.rank:
        # ── Generate final recommendations ────────────────────────────────
        recommendations = recommend(
            student_rank=profile.rank,
            branch=result.top_branch,
            budget_lakh=profile.budget_lakh,
            preferred_location=profile.preferred_location,
        )

        # Enrich with Reddit insights (best-effort, logged on failure)
        for college_rec in recommendations[:6]:  # Only enrich top 6
            try:
                raw_text = await fetch_college_insights(college_rec.name)
                if raw_text:
                    bullets = await summarize_reddit_insights(college_rec.name, raw_text)
                    college_rec.reddit_insights = bullets
            except Exception as e:
                logger.warning(f"Reddit enrichment failed for {college_rec.name}: {e}")

        report = build_counselling_report(profile, result, recommendations)
        profile.is_complete = True

        final_msg = (
            f"🎉 Here are your personalised college recommendations! "
            f"I've classified {len(recommendations)} colleges across Dream, Moderate, and Safe tiers "
            f"based on your JEE rank of {profile.rank} and aptitude for **{result.top_branch} Engineering**."
        )
        profile.add_message("assistant", final_msg)

        logger.info({"event": "session_complete", "session_id": profile.session_id})
        return ChatResponse(
            session_id=profile.session_id,
            assistant_message=final_msg,
            next_question=None,
            branch_scores=result.normalized_scores,
            overall_confidence=result.confidence,
            current_category="CONFIRMATION",
            is_complete=True,
            report=report,
        )

    # ── Regular flow: get next question ───────────────────────────────────
    next_q = select_next_question(profile)
    profile_summary: Optional[str] = None

    if is_confirmation:
        # If they made a correction, re-evaluate to get updated top_branch
        result = evaluate(profile.cumulative_signals)
        profile_summary = build_profile_summary(profile, result)
        
        if forced_override:
            assistant_msg = f"Got it, I've manually updated your best-fit branch! Please review the updated profile below.\n\n{profile_summary}"
        else:
            # Generate a conversational acknowledgement, but append the summary so it's strictly visible.
            ai_reply = await generate_counsellor_response(
                question="Please review the updated summary and confirm if it is correct by typing 'yes'.",
                conversation_history=profile.get_conversation_text(last_n=4),
            )
            assistant_msg = f"{ai_reply}\n\n{profile_summary}"
    elif next_q:
        assistant_msg = await generate_counsellor_response(
            question=next_q["text"],
            conversation_history=profile.get_conversation_text(last_n=4),
        )
    else:
        assistant_msg = "I have everything I need! Type 'yes' to see your results."

    profile.add_message("assistant", assistant_msg)

    return ChatResponse(
        session_id=profile.session_id,
        assistant_message=assistant_msg,
        next_question=next_q["text"] if next_q else None,
        branch_scores=result.normalized_scores,
        overall_confidence=result.confidence,
        current_category=profile.current_category,
        is_complete=False,
        profile_summary=profile_summary,
    )


@app.post("/what-if")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def what_if_simulation(request: Request, body: WhatIfRequest):
    """Simulate recommendations for a hypothetical rank."""
    profile = _get_session(body.session_id)
    branch = profile.recommended_branch or "CS"

    recommendations = recommend(
        student_rank=body.hypothetical_rank,
        branch=branch,
        budget_lakh=profile.budget_lakh,
        preferred_location=profile.preferred_location,
    )

    from services.explanation import build_counselling_report
    from engines.rule_engine import evaluate

    result = evaluate(profile.cumulative_signals or {})
    report = build_counselling_report(profile, result, recommendations)

    return {
        "hypothetical_rank": body.hypothetical_rank,
        "colleges": report["colleges"],
        "total_colleges": report["total_colleges"],
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clear a session (restart flow)."""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared", "session_id": session_id}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get the current session state."""
    profile = _get_session(session_id)
    return {
        "session_id": profile.session_id,
        "current_category": profile.current_category,
        "rank": profile.rank,
        "budget_lakh": profile.budget_lakh,
        "preferred_location": profile.preferred_location,
        "branch_scores": profile.branch_scores.model_dump(),
        "overall_confidence": profile.overall_confidence,
        "recommended_branch": profile.recommended_branch,
        "is_complete": profile.is_complete,
        "message_count": len(profile.messages),
    }


@app.get("/branches")
async def list_branches():
    return {"branches": get_available_branches()}
