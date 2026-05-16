#!/usr/bin/env python3
"""
Working main.py - simplified version that actually works
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid
import re
import logging
from datetime import datetime
from typing import Optional

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pathfinder")

# Create app without complex lifespan
app = FastAPI(
    title="Pathfinder AI Career Counsellor",
    description="AI counselling API for Indian engineering students",
    version="1.0.0",
)

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import only what we need, when we need it
def get_conversation_controller():
    from engines.conversation_controller import conversation_controller
    return conversation_controller

def get_session_manager():
    from engines.session_manager import session_manager
    return session_manager

# Request/Response models
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

# Helper functions
def sanitize_input(text: str, max_len: int = 2000) -> str:
    text = text.strip()[:max_len]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def _extract_rank(text: str) -> Optional[int]:
    match = re.search(r'\b(\d{1,6})\b', text)
    if match:
        val = int(match.group(1))
        if 1 <= val <= 999_999:
            return val
    return None

def _extract_budget(text: str) -> Optional[float]:
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

# Routes
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

@app.get("/api/llm-status")
async def llm_status():
    """Check which LLM provider is active"""
    try:
        from services.llm_client import check_llm_health
        return check_llm_health()
    except Exception as e:
        return {"error": str(e), "status": "unavailable"}

@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: Request):
    """Create a new counselling session"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Generate unique session ID
    session_id = f"{uuid.uuid4()}-{int(datetime.utcnow().timestamp() * 1000)}"
    
    logger.info(f"Creating new session: {session_id}")

    # Parse optional data
    rank: Optional[int] = None
    budget_lakh: Optional[float] = None
    preferred_location: Optional[str] = None

    raw_rank = body.get("jee_rank") or body.get("kcet_rank") or body.get("neet_rank")
    if raw_rank is not None:
        try:
            rank = int(raw_rank)
        except (ValueError, TypeError):
            pass

    raw_budget = body.get("budget_lakh")
    if raw_budget is not None:
        try:
            budget_lakh = float(raw_budget)
        except (ValueError, TypeError):
            pass

    raw_location = body.get("preferred_location")
    if raw_location and str(raw_location).strip():
        preferred_location = str(raw_location).strip()

    # Start conversation
    controller = get_conversation_controller()
    _q_id, first_question_text = await controller.start_conversation(
        session_id=session_id,
        rank=rank,
        budget_lakh=budget_lakh,
        preferred_location=preferred_location,
    )

    prefilled_parts = []
    if rank:
        prefilled_parts.append("rank")
    if budget_lakh:
        prefilled_parts.append("budget")
    if preferred_location:
        prefilled_parts.append("location")

    welcome = (
        "👋 Hi! I'm Pathfinder, your AI career counsellor. "
        + (
            f"Thanks for sharing your {', '.join(prefilled_parts)} upfront — I've saved that info. "
            if prefilled_parts
            else ""
        )
        + "I'll ask you a few questions to figure out the best engineering branch and colleges for you. Let's start!"
    )

    return StartSessionResponse(
        session_id=session_id,
        first_question=first_question_text,
        message=welcome,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """Process a user message and return the next counsellor response"""
    user_text = sanitize_input(body.user_message)
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    logger.info(f"Chat - Session: {body.session_id[:8]}... | Message: {user_text[:50]}...")

    # Get session
    session_manager = get_session_manager()
    fsm_state = session_manager.get_session(body.session_id)
    if not fsm_state:
        logger.warning(f"Session not found: {body.session_id[:8]}...")
        raise HTTPException(
            status_code=404,
            detail=f"Session not found. Please start a new session.",
        )

    # Extract rank/budget from message if not set
    if fsm_state.rank is None:
        rank_val = _extract_rank(user_text)
        if rank_val:
            fsm_state.rank = rank_val

    if fsm_state.budget_lakh is None:
        budget_val = _extract_budget(user_text)
        if budget_val:
            fsm_state.budget_lakh = budget_val

    if fsm_state.preferred_location is None:
        words = [w for w in user_text.split() if len(w) > 3]
        if words:
            fsm_state.preferred_location = words[0].title()

    session_manager.update_session(fsm_state)

    # Process message with timeout protection
    controller = get_conversation_controller()
    try:
        import asyncio
        # Add timeout to the entire chat processing
        result = await asyncio.wait_for(
            controller.process_message(
                session_id=body.session_id,
                user_message=user_text,
            ),
            timeout=8.0  # 8 second timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Chat processing timed out for session {body.session_id[:8]}...")
        # Return a fallback response
        return ChatResponse(
            session_id=body.session_id,
            assistant_message="I'm processing your response. While I work on that, could you tell me more about what subjects you enjoy?",
            next_question="What are your favorite subjects in school, and what activities do you enjoy outside of studies?",
            branch_scores={"CS": 0.5, "Electronics": 0.5, "Mechanical": 0.5, "Civil": 0.5},
            overall_confidence=0.3,
            current_category="interest_assessment",
            is_complete=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Chat processing error: {exc}")
        # Return a fallback response
        return ChatResponse(
            session_id=body.session_id,
            assistant_message="I'm having trouble processing that. Could you tell me about your interests in engineering?",
            next_question="What subjects or activities do you enjoy most?",
            branch_scores={"CS": 0.5, "Electronics": 0.5, "Mechanical": 0.5, "Civil": 0.5},
            overall_confidence=0.5,
            current_category="interest_assessment",
            is_complete=False,
        )

    # Handle completion
    if result["is_complete"]:
        final_msg = "🎉 Based on our conversation, I have your recommendations ready!"
        return ChatResponse(
            session_id=body.session_id,
            assistant_message=final_msg,
            next_question=None,
            branch_scores=result["branch_scores"],
            overall_confidence=result["confidence"],
            current_category=result["stage"],
            is_complete=True,
        )

    # Generate response
    next_question_text = result.get("question_text")
    assistant_msg = next_question_text or "Tell me more about your interests."

    # Try to enhance with AI if available
    try:
        from services.ai_service import generate_counsellor_response
        enhanced_msg = await generate_counsellor_response(
            question=next_question_text or assistant_msg,
            conversation_history=user_text,
        )
        if enhanced_msg and len(enhanced_msg) > 10:
            assistant_msg = enhanced_msg
    except Exception as e:
        logger.warning(f"AI enhancement failed, using fallback: {e}")

    return ChatResponse(
        session_id=body.session_id,
        assistant_message=assistant_msg,
        next_question=next_question_text,
        branch_scores=result["branch_scores"],
        overall_confidence=result["confidence"],
        current_category=result["stage"],
        is_complete=False,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)