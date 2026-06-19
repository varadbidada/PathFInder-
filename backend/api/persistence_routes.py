"""
API routes for retrieving persisted data from MongoDB.
These are non-intrusive additions that don't modify existing functionality.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from services.persistence_service import persistence_service

router = APIRouter(prefix="/api/persistence", tags=["persistence"])


@router.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile by user_id."""
    user = await persistence_service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/chat-history/{user_id}")
async def get_user_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 100
):
    """Get chat history for a user, optionally filtered by session_id."""
    history = await persistence_service.get_chat_history(user_id, session_id, limit)
    return {
        "user_id": user_id,
        "session_id": session_id,
        "total_messages": len(history),
        "messages": history
    }


@router.get("/session/{session_id}/conversation")
async def get_session_conversation(session_id: str):
    """Get complete conversation for a specific session."""
    conversation = await persistence_service.get_session_conversation(session_id)
    return {
        "session_id": session_id,
        "total_messages": len(conversation),
        "conversation": conversation
    }


@router.get("/resumes/{user_id}")
async def get_user_resumes(user_id: str, limit: int = 10):
    """Get all resumes for a user."""
    resumes = await persistence_service.get_user_resumes(user_id, limit)
    return {
        "user_id": user_id,
        "total_resumes": len(resumes),
        "resumes": resumes
    }


@router.get("/roadmaps/{user_id}")
async def get_user_roadmaps(user_id: str, limit: int = 10):
    """Get all learning roadmaps for a user."""
    roadmaps = await persistence_service.get_user_roadmaps(user_id, limit)
    return {
        "user_id": user_id,
        "total_roadmaps": len(roadmaps),
        "roadmaps": roadmaps
    }


@router.get("/assessments/{user_id}")
async def get_user_assessments(user_id: str, limit: int = 10):
    """Get all skill assessments for a user."""
    assessments = await persistence_service.get_user_assessments(user_id, limit)
    return {
        "user_id": user_id,
        "total_assessments": len(assessments),
        "assessments": assessments
    }


@router.get("/internships/{user_id}")
async def get_user_internships(user_id: str, limit: int = 20):
    """Get internship recommendations for a user."""
    internships = await persistence_service.get_user_internship_recommendations(user_id, limit)
    return {
        "user_id": user_id,
        "total_recommendations": len(internships),
        "recommendations": internships
    }


@router.post("/internships/{recommendation_id}/apply")
async def mark_internship_applied(recommendation_id: str):
    """Mark an internship as applied."""
    success = await persistence_service.mark_internship_applied(recommendation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"success": True, "recommendation_id": recommendation_id}


@router.put("/roadmaps/{roadmap_id}/progress")
async def update_roadmap_progress(
    roadmap_id: str,
    progress_percentage: float,
    completed_milestones: list[str]
):
    """Update progress on a learning roadmap."""
    success = await persistence_service.update_roadmap_progress(
        roadmap_id,
        progress_percentage,
        completed_milestones
    )
    if not success:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return {
        "success": True,
        "roadmap_id": roadmap_id,
        "progress_percentage": progress_percentage
    }


@router.get("/user-summary/{user_id}")
async def get_user_summary(user_id: str):
    """Get a comprehensive summary of all user data."""
    profile = await persistence_service.get_user_profile(user_id)
    chat_history = await persistence_service.get_chat_history(user_id, limit=50)
    resumes = await persistence_service.get_user_resumes(user_id, limit=5)
    roadmaps = await persistence_service.get_user_roadmaps(user_id, limit=5)
    assessments = await persistence_service.get_user_assessments(user_id, limit=5)
    internships = await persistence_service.get_user_internship_recommendations(user_id, limit=10)
    
    return {
        "user_id": user_id,
        "profile": profile,
        "statistics": {
            "total_chat_messages": len(chat_history),
            "total_resumes": len(resumes),
            "total_roadmaps": len(roadmaps),
            "total_assessments": len(assessments),
            "total_internship_recommendations": len(internships)
        },
        "recent_activity": {
            "recent_chats": chat_history[:5],
            "recent_resumes": resumes[:2],
            "recent_roadmaps": roadmaps[:2],
            "recent_assessments": assessments[:2]
        }
    }
