"""
Middleware to automatically persist data to MongoDB without disrupting existing flows.
This integrates seamlessly with the existing session management.
"""
import logging
import uuid
from typing import Any, Optional
from datetime import datetime
from services.persistence_service import persistence_service

logger = logging.getLogger(__name__)


async def persist_session_start(
    session_id: str,
    user_id: Optional[str],
    session_data: dict[str, Any]
) -> None:
    """
    Persist session start data to MongoDB.
    Extracts user profile information from session data.
    """
    try:
        if not user_id:
            user_id = session_id  # Use session_id as user_id if not provided
        
        # Extract user profile data from session
        engine_state = session_data.get("engine_state", {})
        raw_form = session_data.get("raw_form", {})
        
        user_profile_data = {
            "user_id": user_id,
            "jee_rank": engine_state.get("rank"),
            "budget_lakh": engine_state.get("budget_lakh"),
            "preferred_location": engine_state.get("preferred_location"),
            "exam_type": engine_state.get("exam_type"),
            "email": raw_form.get("email"),
            "name": raw_form.get("name"),
        }
        
        # Save/update user profile
        await persistence_service.save_user_profile(**user_profile_data)
        logger.info(f"✅ Persisted session start for user: {user_id}")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist session start: {e}")
        # Don't raise - persistence failure shouldn't break the app


async def persist_chat_exchange(
    session_id: str,
    user_id: Optional[str],
    question: str,
    answer: str,
    branch_scores: Optional[dict[str, float]] = None,
    confidence: Optional[float] = None,
    category: Optional[str] = None,
    student_model_snapshot: Optional[dict[str, Any]] = None
) -> None:
    """
    Persist a chat exchange (question-answer pair) to MongoDB.
    Includes optional student_model_snapshot for LLM-powered engine.
    """
    try:
        if not user_id:
            user_id = session_id
        
        await persistence_service.save_chat_exchange(
            user_id=user_id,
            session_id=session_id,
            question=question,
            answer=answer,
            branch_scores=branch_scores,
            confidence=confidence,
            category=category,
            student_model_snapshot=student_model_snapshot
        )
        logger.info(f"✅ Persisted chat exchange for session: {session_id[:12]}...")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist chat exchange: {e}")


async def persist_roadmap(
    user_id: Optional[str],
    target_role: str,
    roadmap_data: dict[str, Any]
) -> Optional[str]:
    """
    Persist a generated learning roadmap to MongoDB.
    """
    try:
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        roadmap_id = await persistence_service.save_learning_roadmap(
            user_id=user_id,
            target_role=target_role,
            current_level=roadmap_data.get("current_level", "beginner"),
            milestones=roadmap_data.get("milestones", []),
            timeline_weeks=roadmap_data.get("timeline_weeks", 12),
            skills_to_learn=roadmap_data.get("skills_to_learn", []),
            resources=roadmap_data.get("resources", [])
        )
        logger.info(f"✅ Persisted roadmap: {roadmap_id}")
        return roadmap_id
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist roadmap: {e}")
        return None


async def persist_skill_assessment(
    user_id: Optional[str],
    assessment_data: dict[str, Any]
) -> Optional[str]:
    """
    Persist skill assessment results to MongoDB.
    """
    try:
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        assessment_id = await persistence_service.save_skill_assessment(
            user_id=user_id,
            skill_category=assessment_data.get("skill_category", "general"),
            overall_score=assessment_data.get("overall_score", 0.0),
            skill_scores=assessment_data.get("skill_scores", {}),
            strengths=assessment_data.get("strengths", []),
            weaknesses=assessment_data.get("weaknesses", []),
            skill_gaps=assessment_data.get("skill_gaps", []),
            recommended_learning_paths=assessment_data.get("recommended_learning_paths", [])
        )
        logger.info(f"✅ Persisted skill assessment: {assessment_id}")
        return assessment_id
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist skill assessment: {e}")
        return None


async def persist_resume_analysis(
    user_id: Optional[str],
    filename: str,
    file_size: int,
    analysis_data: dict[str, Any]
) -> Optional[str]:
    """
    Persist resume analysis results to MongoDB.
    """
    try:
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        resume_id = await persistence_service.save_resume_analysis(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            extracted_text=analysis_data.get("extracted_text"),
            skills=analysis_data.get("skills", []),
            ats_score=analysis_data.get("ats_score"),
            ai_feedback=analysis_data.get("ai_feedback"),
            recommendations=analysis_data.get("recommendations", []),
            missing_skills=analysis_data.get("missing_skills", [])
        )
        logger.info(f"✅ Persisted resume analysis: {resume_id}")
        return resume_id
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist resume analysis: {e}")
        return None


async def persist_internship_recommendations(
    user_id: Optional[str],
    recommendations: list[dict[str, Any]]
) -> Optional[list[str]]:
    """
    Persist internship recommendations to MongoDB.
    """
    try:
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        recommendation_ids = await persistence_service.save_internship_recommendations(
            user_id=user_id,
            recommendations=recommendations
        )
        logger.info(f"✅ Persisted {len(recommendation_ids)} internship recommendations")
        return recommendation_ids
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to persist internship recommendations: {e}")
        return None


def extract_user_id_from_request(request: Any, session_id: str) -> str:
    """
    Extract user ID from request headers or use session_id as fallback.
    Can be extended to support authentication tokens.
    """
    # Check for user_id in headers
    user_id = request.headers.get("X-User-ID")
    
    # Check for user_id in cookies
    if not user_id:
        user_id = request.cookies.get("user_id")
    
    # Fallback to session_id
    if not user_id:
        user_id = session_id
    
    return user_id
