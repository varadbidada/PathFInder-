#!/usr/bin/env python3
"""
Simplified main.py to isolate the hanging issue
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime

# Simple app without lifespan or complex middleware
app = FastAPI(title="Pathfinder Simple")

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartSessionResponse(BaseModel):
    session_id: str
    first_question: str
    message: str

class ChatRequest(BaseModel):
    session_id: str
    user_message: str

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-simple",
    }

@app.post("/session/start", response_model=StartSessionResponse)
async def start_session():
    """Create a new session without complex logic"""
    session_id = f"{uuid.uuid4()}-{int(datetime.utcnow().timestamp() * 1000)}"
    
    return StartSessionResponse(
        session_id=session_id,
        first_question="Hi! I'm Pathfinder. Ready to start?",
        message="Welcome! Let's find your perfect engineering branch.",
    )

@app.post("/chat")
async def chat(body: ChatRequest):
    """Simple chat without AI processing"""
    return {
        "session_id": body.session_id,
        "assistant_message": f"You said: {body.user_message}. This is a simple echo response.",
        "next_question": "What would you like to tell me next?",
        "branch_scores": {"CS": 0.8, "Electronics": 0.6},
        "overall_confidence": 0.7,
        "current_category": "test",
        "is_complete": False,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)