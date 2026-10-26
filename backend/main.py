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

# Import both engines
from engines.adaptive_engine import AdaptiveQuestionEngine
from engines.adaptive_engine_llm import LLMAdaptiveEngine
from engines.recommendation import recommend

# Import LLM client as a module to pass to LLM engine
import services.llm_client as llm_client

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

# Initialize engines
deterministic_engine = AdaptiveQuestionEngine()
llm_engine = LLMAdaptiveEngine()

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

    # Determine which engine was used
    if "student_model" in session.get("engine_state", {}):
        # LLM engine
        rank = session["engine_state"].get("rank")
        exam_type = session["engine_state"].get("exam_type")
    else:
        # Deterministic engine
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


def compose_final_report_deterministic(session: dict[str, Any]) -> dict[str, Any]:
    """Compose report for deterministic engine."""
    engine_state = session["engine_state"]
    engine_report = deterministic_engine.build_report(engine_state)
    recommended_branch = engine_report.get("recommended_branch")
    colleges_by_tier, total_colleges = build_college_report(session, recommended_branch)

    return {
        **engine_report,
        "colleges": colleges_by_tier,
        "total_colleges": total_colleges,
        "student_rank": engine_state.get("rank"),
    }


def compose_final_report_llm(session: dict[str, Any]) -> dict[str, Any]:
    """Compose report for LLM engine."""
    engine_state = session["engine_state"]
    engine_report = llm_engine.build_report(engine_state)
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
    """Check LLM availability and decide which engine to use."""
    health = llm_client.check_llm_health()
    
    # If LLM available, use LLM engine
    if health.get("active_provider"):
        return {
            **health,
            "recommended_engine": "llm",
            "status": "working"
        }
    
    # Otherwise fall back to deterministic
    return {
        **health,
        "recommended_engine": "deterministic",
        "active_provider": "deterministic-engine",
        "active_model": "adaptive-question-engine",
        "status": "working (fallback)"
    }


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: Request):
    """Start new counseling session. Auto-detects LLM availability."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = f"{uuid.uuid4()}-{int(datetime.now(UTC).timestamp() * 1000)}"
    exam_type = normalize_exam_type(body.get("exam_type"))
    rank = select_rank(body, exam_type)

    # Check if LLM is available
    llm_health = llm_client.check_llm_health()
    use_llm = llm_health.get("active_provider") is not None
    
    # Choose engine based on LLM availability
    if use_llm:
        logger.info(f"🤖 Starting LLM-powered session with {llm_health['active_provider']}")
        engine_state = llm_engine.create_session(
            exam_type=exam_type,
            rank=rank,
            budget_lakh=body.get("budget_lakh"),
            preferred_location=body.get("preferred_location"),
        )
        opening_question = llm_engine.select_opening_question(engine_state)
        engine_type = "llm"
    else:
        logger.info("⚙️ Starting deterministic session (LLM unavailable)")
        engine_state = deterministic_engine.create_session(
            exam_type=exam_type,
            rank=rank,
            budget_lakh=body.get("budget_lakh"),
            preferred_location=body.get("preferred_location"),
        )
        opening_question = deterministic_engine.select_opening_question(engine_state)
        engine_type = "deterministic"

    sessions[session_id] = {
        "created_at": datetime.now(UTC).isoformat(),
        "engine_state": engine_state,
        "raw_form": body,
        "engine_type": engine_type,  # Track which engine is being used
    }

    # ========== MongoDB Persistence ==========
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
        "Hi! I'm Pathfinder. " +
        ("I'll ask you some questions to understand your interests and personality. " if use_llm else
         "I'll use a structured adaptive question engine to estimate your best-fit engineering branch. ") +
        (
            f"I've already saved your {', '.join(prefilled_parts)}. "
            if prefilled_parts
            else ""
        ) +
        "Let's start!"
    )

    logger.info(f"Started {engine_type} session {session_id}")
    return StartSessionResponse(
        session_id=session_id,
        first_question=opening_question["text"],
        message=welcome,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    """Process chat message using appropriate engine."""
    user_text = sanitize_input(body.user_message)
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    user_id = extract_user_id_from_request(request, body.session_id)
    engine_type = session.get("engine_type", "deterministic")
    
    # Process with appropriate engine
    if engine_type == "llm":
        result = llm_engine.process_answer(
            session["engine_state"],
            user_text,
            llm_client  # Pass the module as client
        )
        
        # Extract student_model snapshot for persistence
        student_model_snapshot = result.get("student_model")
        if student_model_snapshot and hasattr(student_model_snapshot, 'to_dict'):
            student_model_snapshot = student_model_snapshot.to_dict()
        elif isinstance(student_model_snapshot, dict):
            pass  # Already a dict
        else:
            student_model_snapshot = None
        
        # Log trait coverage for debugging
        if student_model_snapshot:
            turn = session["engine_state"]["turn_number"]
            uncovered = llm_engine.get_uncovered_traits(result["student_model"])
            logger.info(f"[COVERAGE] Turn {turn}: {uncovered['total_uncovered']} uncovered traits")
            logger.info(f"[COVERAGE] Numeric: {uncovered['numeric']}")
            logger.info(f"[COVERAGE] Categorical: {uncovered['categorical']}")
            logger.info(f"[CONFIDENCE] {result['confidence']:.2f} / 0.85 needed")
            logger.info(f"[HYPOTHESIS] {result['student_model'].branch_hypothesis}")
    else:
        result = deterministic_engine.process_answer(session["engine_state"], user_text)
        student_model_snapshot = None

    # Handle completion
    if result["is_complete"]:
        if engine_type == "llm":
            report = compose_final_report_llm(session)
        else:
            report = compose_final_report_deterministic(session)
        
        recommended_branch = report.get("recommended_branch") or "a broad engineering path"
        assistant_message = (
            f"Based on your answers, {recommended_branch} is your strongest fit. "
            f"Current confidence is {round(result['confidence'] * 100):.0f}%."
        )
        if report["total_colleges"] > 0:
            assistant_message += f" I also found {report['total_colleges']} matching colleges."

        # Persist final exchange
        await persist_chat_exchange(
            session_id=body.session_id,
            user_id=user_id,
            question=user_text,
            answer=assistant_message,
            branch_scores=result["branch_scores"],
            confidence=result["confidence"],
            category="COMPLETED",
            student_model_snapshot=student_model_snapshot
        )

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

    # Continue conversation
    next_question = result["question"]
    
    # Build debug info for LLM engine
    debug_info = {}
    if engine_type == "llm" and result.get("student_model"):
        uncovered = llm_engine.get_uncovered_traits(result["student_model"])
        debug_info = {
            "turn": session["engine_state"]["turn_number"],
            "uncovered_traits": uncovered,
            "confidence": result["confidence"],
            "hypothesis": result["student_model"].branch_hypothesis,
            "target_trait": result.get("target_trait", "unknown")
        }
    
    # Persist exchange
    await persist_chat_exchange(
        session_id=body.session_id,
        user_id=user_id,
        question=user_text,
        answer=next_question["text"],
        branch_scores=result["branch_scores"],
        confidence=result["confidence"],
        category=session["engine_state"].get("current_category", session["engine_state"].get("current_stage", "unknown")),
        student_model_snapshot=student_model_snapshot
    )
    
    response_data = ChatResponse(
        session_id=body.session_id,
        assistant_message=next_question["text"],
        next_question=next_question["text"],
        branch_scores=result["branch_scores"],
        overall_confidence=result["confidence"],
        current_category=session["engine_state"].get("current_category", session["engine_state"].get("current_stage", "unknown")),
        is_complete=False,
        top_branches=result["top_branches"],
        trait_breakdown=result["trait_breakdown"],
    )
    
    # Add debug info if available
    if debug_info:
        response_data_dict = response_data.dict()
        response_data_dict["debug"] = debug_info
        return response_data_dict
    
    return response_data


@app.get("/api/session/{session_id}/model")
async def get_session_model(session_id: str):
    """Get current student model for a session (LLM engine only)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("engine_type") != "llm":
        raise HTTPException(status_code=400, detail="Student model only available for LLM-powered sessions")
    
    student_model = session["engine_state"].get("student_model")
    if not student_model:
        raise HTTPException(status_code=404, detail="Student model not found")
    
    if hasattr(student_model, 'to_dict'):
        return student_model.to_dict()
    return student_model


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    existed = session_id in sessions
    sessions.pop(session_id, None)
    return {"deleted": existed}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
