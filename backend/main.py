#!/usr/bin/env python3
"""
Final working main.py - bypasses complex logic that's causing hangs
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid
import re
import logging
from datetime import datetime
from typing import Optional, Dict

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pathfinder")

# Create app
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

# Simple in-memory session storage
sessions: Dict[str, Dict] = {}

# Hardcoded questions for reliable flow
QUESTIONS = [
    "What subjects do you enjoy most in school? Tell me about your favorite topics.",
    "Do you prefer working with your hands on practical projects, or solving theoretical problems?",
    "When you think about technology, what excites you most - building apps, understanding how things work, or creating new inventions?",
    "Are you more interested in helping people directly, or working behind the scenes on technical solutions?",
    "What kind of work environment appeals to you - collaborative teams, independent research, or hands-on workshops?",
    "Do you enjoy mathematics and logical problem-solving, or are you more drawn to creative and artistic pursuits?",
    "When you see a complex problem, do you prefer to break it down systematically or brainstorm creative solutions?",
    "Are you interested in how the human body works, or are you more fascinated by machines and technology?",
    "Do you like to build and fix things, or do you prefer to analyze and understand how systems work?",
    "What motivates you more - making a direct impact on people's lives or advancing scientific knowledge?"
]

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
    report: Optional[dict] = None  # Add report field

# Helper functions
def sanitize_input(text: str, max_len: int = 2000) -> str:
    text = text.strip()[:max_len]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def analyze_response(text: str) -> Dict[str, float]:
    """Simple keyword-based analysis to determine branch preferences"""
    text_lower = text.lower()
    
    scores = {
        "CS": 0.5,
        "Electronics": 0.5,
        "Mechanical": 0.5,
        "Civil": 0.5,
        "Medical": 0.5
    }
    
    # CS keywords
    cs_keywords = ["computer", "programming", "coding", "software", "app", "website", "algorithm", "data", "ai", "technology"]
    for keyword in cs_keywords:
        if keyword in text_lower:
            scores["CS"] += 0.1
    
    # Electronics keywords
    electronics_keywords = ["electronics", "circuits", "hardware", "signals", "communication", "embedded", "robotics"]
    for keyword in electronics_keywords:
        if keyword in text_lower:
            scores["Electronics"] += 0.1
    
    # Mechanical keywords
    mechanical_keywords = ["mechanical", "machines", "build", "hands-on", "manufacturing", "design", "automotive", "engine"]
    for keyword in mechanical_keywords:
        if keyword in text_lower:
            scores["Mechanical"] += 0.1
    
    # Civil keywords
    civil_keywords = ["construction", "buildings", "infrastructure", "roads", "bridges", "architecture", "planning"]
    for keyword in civil_keywords:
        if keyword in text_lower:
            scores["Civil"] += 0.1
    
    # Medical keywords
    medical_keywords = ["medical", "doctor", "health", "biology", "human", "body", "medicine", "patient", "care"]
    for keyword in medical_keywords:
        if keyword in text_lower:
            scores["Medical"] += 0.1
    
    # Normalize scores
    max_score = max(scores.values())
    if max_score > 1.0:
        for key in scores:
            scores[key] = min(scores[key], 1.0)
    
    return scores

# Routes
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "active_sessions": len(sessions),
    }

@app.get("/api/llm-status")
async def llm_status():
    """Check LLM status - simplified version"""
    return {
        "groq": False,
        "ollama": True,
        "ollama_model": "llama3.2:3b",
        "active_provider": "simplified",
        "active_model": "rule-based",
        "status": "working"
    }

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

    # Initialize session
    sessions[session_id] = {
        "question_index": 0,
        "responses": [],
        "branch_scores": {"CS": 0.5, "Electronics": 0.5, "Mechanical": 0.5, "Civil": 0.5, "Medical": 0.5},
        "rank": body.get("jee_rank"),
        "budget": body.get("budget_lakh"),
        "location": body.get("preferred_location"),
        "created_at": datetime.utcnow().isoformat()
    }

    first_question = QUESTIONS[0]
    
    prefilled_parts = []
    if body.get("jee_rank"):
        prefilled_parts.append("rank")
    if body.get("budget_lakh"):
        prefilled_parts.append("budget")
    if body.get("preferred_location"):
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
        first_question=first_question,
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
    if body.session_id not in sessions:
        logger.warning(f"Session not found: {body.session_id[:8]}...")
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please start a new session.",
        )

    session = sessions[body.session_id]
    
    # Analyze the response
    response_scores = analyze_response(user_text)
    
    # Update session scores (weighted average)
    for branch in session["branch_scores"]:
        session["branch_scores"][branch] = (
            session["branch_scores"][branch] * 0.7 + response_scores[branch] * 0.3
        )
    
    # Store response
    session["responses"].append(user_text)
    session["question_index"] += 1
    
    # Check if we should complete
    if session["question_index"] >= len(QUESTIONS) or session["question_index"] >= 5:
        # Find top branch
        top_branch = max(session["branch_scores"], key=session["branch_scores"].get)
        confidence = session["branch_scores"][top_branch]
        
        # Generate college recommendations if we have rank data
        colleges_by_tier = {"Dream": [], "Moderate": [], "Safe": []}
        total_colleges = 0
        
        if session.get("rank"):
            try:
                # Import the recommendation function
                from engines.recommendation import recommend
                
                # Determine rank type based on rank value (simple heuristic)
                rank_type = "jee_advanced" if session["rank"] <= 50000 else "jee_main"
                
                # Get recommendations
                recommendations = recommend(
                    student_rank=session["rank"],
                    branch=top_branch,
                    budget_lakh=session.get("budget"),
                    preferred_location=session.get("location"),
                    rank_type=rank_type,
                    max_results_per_tier=5
                )
                
                # Group by tier
                for rec in recommendations:
                    tier = rec.recommendation_tier
                    if tier in colleges_by_tier:
                        # Convert to dict for JSON serialization
                        college_dict = {
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
                            "reddit_insights": getattr(rec, 'reddit_insights', []),
                        }
                        colleges_by_tier[tier].append(college_dict)
                        total_colleges += 1
                        
                logger.info(f"Generated {total_colleges} college recommendations for {top_branch}")
                        
            except Exception as e:
                logger.error(f"Failed to generate college recommendations: {e}")
                # Continue without college recommendations
        
        # Create report object
        report = {
            "recommended_branch": top_branch,
            "branch_scores": session["branch_scores"],
            "confidence": confidence,
            "colleges": colleges_by_tier,
            "total_colleges": total_colleges,
            "student_rank": session.get("rank"),
            "branch_summary": f"Based on your responses, {top_branch} Engineering aligns well with your interests and aptitudes.",
        }
        
        final_msg = f"🎉 Based on our conversation, I recommend **{top_branch} Engineering** for you! Your aptitude and interests align well with this field."
        
        if total_colleges > 0:
            final_msg += f" I've found {total_colleges} colleges that match your profile across Dream, Moderate, and Safe categories."
        
        return ChatResponse(
            session_id=body.session_id,
            assistant_message=final_msg,
            next_question=None,
            branch_scores=session["branch_scores"],
            overall_confidence=confidence,
            current_category="completed",
            is_complete=True,
            report=report,  # Add the report to the response
        )
    
    # Get next question
    next_question = QUESTIONS[session["question_index"]]
    
    # Generate a natural response
    assistant_msg = f"That's interesting! {next_question}"
    
    # Calculate overall confidence
    scores = list(session["branch_scores"].values())
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)
    confidence = (max_score - avg_score) * 2  # Confidence based on separation
    
    return ChatResponse(
        session_id=body.session_id,
        assistant_message=assistant_msg,
        next_question=next_question,
        branch_scores=session["branch_scores"],
        overall_confidence=min(confidence, 1.0),
        current_category="interest_assessment",
        is_complete=False,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)