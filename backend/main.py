#!/usr/bin/env python3
from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engines.adaptive_engine import AdaptiveQuestionEngine
from engines.recommendation import recommend

# MongoDB imports
from database.connection import connect_to_database, close_database_connection, check_database_health
from middleware.persistence_middleware import (
    persist_session_start,
    persist_chat_exchange,
    extract_user_id_from_request
)
from api.persistence_routes import router as persistence_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pathfinder")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """MongoDB connection lifecycle management."""
    # Startup: Connect to MongoDB
    logger.info("🚀 Starting Pathfinder application...")
    try:
        await connect_to_database()
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.warning("⚠️  Application will continue without persistence")
    
    yield
    
    # Shutdown: Close MongoDB connection
    logger.info("🛑 Shutting down Pathfinder application...")
    await close_database_connection()
    logger.info("✅ Application shutdown complete")


app = FastAPI(
    title="Pathfinder AI Career Counsellor",
    description="Adaptive engineering branch fit engine for Pathfinder",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include persistence API routes
app.include_router(persistence_router)

engine = AdaptiveQuestionEngine()
sessions: dict[str, dict[str, Any]] = {}


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
    report: Optional[dict[str, Any]] = None
    top_branches: list[dict[str, Any]] = Field(default_factory=list)
    trait_breakdown: dict[str, float] = Field(default_factory=dict)


def sanitize_input(text: str, max_len: int = 2000) -> str:
    text = text.strip()[:max_len]
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def normalize_exam_type(raw_exam_type: str | None) -> str:
    exam = (raw_exam_type or "").strip().lower()
    if "advanced" in exam:
        return "jee_advanced"
    if "state" in exam or "kcet" in exam or "cet" in exam:
        return "state_exam"
    if "neet" in exam:
        return "neet"
    return "jee_main"


def select_rank(form_data: dict[str, Any], exam_type: str) -> int | None:
    if exam_type in {"jee_main", "jee_advanced"}:
        return form_data.get("jee_rank")
    if exam_type == "state_exam":
        return form_data.get("kcet_rank") or form_data.get("jee_rank")
    if exam_type == "neet":
        return form_data.get("neet_rank")
    return form_data.get("jee_rank")


def build_college_report(session: dict[str, Any], recommended_branch: str | None) -> tuple[dict[str, list[dict[str, Any]]], int]:
    colleges_by_tier: dict[str, list[dict[str, Any]]] = {
        "Dream": [],
        "Moderate": [],
        "Safe": [],
    }
    total_colleges = 0

    if not recommended_branch:
        return colleges_by_tier, total_colleges

    rank = session["engine_state"].get("rank")
    exam_type = session["engine_state"].get("exam_type")
    if not rank or exam_type not in {"jee_main", "jee_advanced"}:
        return colleges_by_tier, total_colleges

    try:
        recommendations = recommend(
            student_rank=rank,
            branch=recommended_branch,
            budget_lakh=session["engine_state"].get("budget_lakh"),
            preferred_location=session["engine_state"].get("preferred_location"),
            rank_type=exam_type,
            max_results_per_tier=5,
        )
    except Exception as exc:
        logger.error("Failed to generate college recommendations: %s", exc)
        return colleges_by_tier, total_colleges

    for rec in recommendations:
        tier = rec.recommendation_tier
        colleges_by_tier[tier].append(
            {
                "id": rec.id,
                "name": rec.name,
                "branch": rec.branch,
                "location": rec.location,
                "cutoff_rank": rec.cutoff_rank,
                "annual_fees": rec.annual_fees,
                "placement_avg": rec.placement_avg,
                "recommendation_tier": rec.recommendation_tier,
                "rank_gap": rec.rank_gap,
                "cutoff_source": rec.cutoff_source,
                "low_confidence": rec.low_confidence,
                "reddit_insights": getattr(rec, "reddit_insights", []),
            }
        )
        total_colleges += 1

    return colleges_by_tier, total_colleges


def compose_final_report(session: dict[str, Any]) -> dict[str, Any]:
    engine_state = session["engine_state"]
    engine_report = engine.build_report(engine_state)
    recommended_branch = engine_report.get("recommended_branch")
    colleges_by_tier, total_colleges = build_college_report(session, recommended_branch)

    return {
        **engine_report,
        "colleges": colleges_by_tier,
        "total_colleges": total_colleges,
        "student_rank": engine_state.get("rank"),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with MongoDB status."""
    mongo_health = await check_database_health()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "2.0.0",
        "active_sessions": len(sessions),
        "mongodb": mongo_health,
    }


@app.get("/api/llm-status")
async def llm_status():
    return {
        "groq": False,
        "ollama": False,
        "ollama_model": None,
        "active_provider": "deterministic-engine",
        "active_model": "adaptive-question-engine",
        "status": "working",
    }


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = f"{uuid.uuid4()}-{int(datetime.now(UTC).timestamp() * 1000)}"
    exam_type = normalize_exam_type(body.get("exam_type"))
    rank = select_rank(body, exam_type)

    engine_state = engine.create_session(
        exam_type=exam_type,
        rank=rank,
        budget_lakh=body.get("budget_lakh"),
        preferred_location=body.get("preferred_location"),
    )
    opening_question = engine.select_opening_question(engine_state)

    sessions[session_id] = {
        "created_at": datetime.now(UTC).isoformat(),
        "engine_state": engine_state,
        "raw_form": body,
    }

    # ========== MongoDB Persistence ==========
    # Persist session start and user profile
    user_id = extract_user_id_from_request(request, session_id)
    await persist_session_start(session_id, user_id, sessions[session_id])
    # =========================================

    prefilled_parts = []
    if rank:
        prefilled_parts.append("rank")
    if body.get("budget_lakh"):
        prefilled_parts.append("budget")
    if body.get("preferred_location"):
        prefilled_parts.append("location")

    welcome = (
        "Hi! I'm Pathfinder. I'll use a structured adaptive question engine to estimate your best-fit engineering branch. "
        + (
            f"I've already saved your {', '.join(prefilled_parts)}. "
            if prefilled_parts
            else ""
        )
        + "Let's start with the most informative question."
    )

    logger.info("Started adaptive session %s", session_id)
    return StartSessionResponse(
        session_id=session_id,
        first_question=opening_question["text"],
        message=welcome,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    user_text = sanitize_input(body.user_message)
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    # ========== MongoDB Persistence ==========
    # Extract user_id for persistence
    user_id = extract_user_id_from_request(request, body.session_id)
    # =========================================

    result = engine.process_answer(session["engine_state"], user_text)

    if result["is_complete"]:
        report = compose_final_report(session)
        recommended_branch = report.get("recommended_branch") or "a broad engineering path"
        assistant_message = (
            f"Based on your answers, {recommended_branch} is your strongest fit. "
            f"Current confidence is {round(result['confidence'] * 100):.0f}%."
        )
        if report["total_colleges"] > 0:
            assistant_message += f" I also found {report['total_colleges']} matching colleges."

        # ========== MongoDB Persistence ==========
        # Persist the final exchange
        await persist_chat_exchange(
            session_id=body.session_id,
            user_id=user_id,
            question=user_text,
            answer=assistant_message,
            branch_scores=result["branch_scores"],
            confidence=result["confidence"],
            category="COMPLETED"
        )
        # =========================================

        return ChatResponse(
            session_id=body.session_id,
            assistant_message=assistant_message,
            next_question=None,
            branch_scores=result["branch_scores"],
            overall_confidence=result["confidence"],
            current_category="COMPLETED",
            is_complete=True,
            report=report,
            top_branches=result["top_branches"],
            trait_breakdown=result["trait_breakdown"],
        )

    next_question = result["question"]
    
    # ========== MongoDB Persistence ==========
    # Persist the question-answer exchange
    await persist_chat_exchange(
        session_id=body.session_id,
        user_id=user_id,
        question=user_text,
        answer=next_question["text"],
        branch_scores=result["branch_scores"],
        confidence=result["confidence"],
        category=session["engine_state"]["current_category"]
    )
    # =========================================
    
    return ChatResponse(
        session_id=body.session_id,
        assistant_message=next_question["text"],
        next_question=next_question["text"],
        branch_scores=result["branch_scores"],
        overall_confidence=result["confidence"],
        current_category=session["engine_state"]["current_category"],
        is_complete=False,
        top_branches=result["top_branches"],
        trait_breakdown=result["trait_breakdown"],
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    existed = session_id in sessions
    sessions.pop(session_id, None)
    return {"deleted": existed}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
