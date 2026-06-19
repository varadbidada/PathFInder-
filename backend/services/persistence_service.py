"""
Persistence service layer for Pathfinder AI Career Counselor.
Provides high-level API for data persistence operations.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Any
from database.connection import get_database
from database.repositories import (
    UserRepository,
    ChatRepository,
    ResumeRepository,
    RoadmapRepository,
    SkillAssessmentRepository,
    InternshipRepository
)

logger = logging.getLogger(__name__)


class PersistenceService:
    """
    Central service for all data persistence operations.
    Abstracts away database implementation details from the main application.
    """
    
    def __init__(self):
        """Initialize repositories (lazy loading)."""
        self._db = None
        self._user_repo = None
        self._chat_repo = None
        self._resume_repo = None
        self._roadmap_repo = None
        self._assessment_repo = None
        self._internship_repo = None
    
    def _ensure_repositories(self):
        """Lazy initialize repositories."""
        if self._db is None:
            self._db = get_database()
            self._user_repo = UserRepository(self._db)
            self._chat_repo = ChatRepository(self._db)
            self._resume_repo = ResumeRepository(self._db)
            self._roadmap_repo = RoadmapRepository(self._db)
            self._assessment_repo = SkillAssessmentRepository(self._db)
            self._internship_repo = InternshipRepository(self._db)
    
    # ==================== User Profile Operations ====================
    
    async def save_user_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs
    ) -> str:
        """Save or update user profile."""
        self._ensure_repositories()
        
        user_data = {
            "user_id": user_id,
            "name": name,
            "email": email,
            **kwargs
        }
        
        return await self._user_repo.upsert_user(user_data)
    
    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile by user_id."""
        self._ensure_repositories()
        return await self._user_repo.get_user(user_id)
    
    async def update_user_from_session(
        self,
        user_id: str,
        session_data: dict[str, Any]
    ) -> bool:
        """Update user profile from counseling session data."""
        self._ensure_repositories()
        
        update_data = {}
        
        # Extract relevant fields from session data
        if "rank" in session_data:
            update_data["jee_rank"] = session_data["rank"]
        if "budget_lakh" in session_data:
            update_data["budget_lakh"] = session_data["budget_lakh"]
        if "preferred_location" in session_data:
            update_data["preferred_location"] = session_data["preferred_location"]
        if "exam_type" in session_data:
            update_data["exam_type"] = session_data["exam_type"]
        
        if update_data:
            return await self._user_repo.update_user(user_id, update_data)
        return False
    
    # ==================== Chat History Operations ====================
    
    async def save_chat_exchange(
        self,
        user_id: str,
        session_id: str,
        question: str,
        answer: str,
        branch_scores: Optional[dict[str, float]] = None,
        confidence: Optional[float] = None,
        category: Optional[str] = None
    ) -> str:
        """Save a question-answer exchange from the conversation."""
        self._ensure_repositories()
        
        chat_data = {
            "chat_id": f"chat_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow(),
            "branch_scores": branch_scores,
            "confidence": confidence,
            "category": category
        }
        
        return await self._chat_repo.save_chat_message(chat_data)
    
    async def get_chat_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """Retrieve chat history for a user."""
        self._ensure_repositories()
        return await self._chat_repo.get_chat_history(user_id, session_id, limit)
    
    async def get_session_conversation(self, session_id: str) -> list[dict]:
        """Get complete conversation for a specific session."""
        self._ensure_repositories()
        return await self._chat_repo.get_session_history(session_id)
    
    # ==================== Resume Analysis Operations ====================
    
    async def save_resume_analysis(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        extracted_text: Optional[str] = None,
        skills: Optional[list[str]] = None,
        ats_score: Optional[float] = None,
        ai_feedback: Optional[str] = None,
        **kwargs
    ) -> str:
        """Save resume analysis results."""
        self._ensure_repositories()
        
        resume_data = {
            "resume_id": f"resume_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "filename": filename,
            "file_size": file_size,
            "extracted_text": extracted_text,
            "skills": skills or [],
            "ats_score": ats_score,
            "ai_feedback": ai_feedback,
            "uploaded_at": datetime.utcnow(),
            "analyzed_at": datetime.utcnow() if ats_score else None,
            **kwargs
        }
        
        return await self._resume_repo.save_resume(resume_data)
    
    async def get_user_resumes(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all resumes for a user."""
        self._ensure_repositories()
        return await self._resume_repo.get_user_resumes(user_id, limit)
    
    # ==================== Roadmap Operations ====================
    
    async def save_learning_roadmap(
        self,
        user_id: str,
        target_role: str,
        current_level: str,
        milestones: list[dict],
        timeline_weeks: int,
        skills_to_learn: list[str],
        **kwargs
    ) -> str:
        """Save a generated learning roadmap."""
        self._ensure_repositories()
        
        roadmap_data = {
            "roadmap_id": f"roadmap_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "target_role": target_role,
            "current_level": current_level,
            "milestones": milestones,
            "timeline_weeks": timeline_weeks,
            "skills_to_learn": skills_to_learn,
            "created_at": datetime.utcnow(),
            **kwargs
        }
        
        return await self._roadmap_repo.save_roadmap(roadmap_data)
    
    async def get_user_roadmaps(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all roadmaps for a user."""
        self._ensure_repositories()
        return await self._roadmap_repo.get_user_roadmaps(user_id, limit)
    
    async def update_roadmap_progress(
        self,
        roadmap_id: str,
        progress_percentage: float,
        completed_milestones: list[str]
    ) -> bool:
        """Update progress on a learning roadmap."""
        self._ensure_repositories()
        
        progress_data = {
            "progress_percentage": progress_percentage,
            "completed_milestones": completed_milestones
        }
        
        return await self._roadmap_repo.update_roadmap_progress(roadmap_id, progress_data)
    
    # ==================== Skill Assessment Operations ====================
    
    async def save_skill_assessment(
        self,
        user_id: str,
        skill_category: str,
        overall_score: float,
        skill_scores: dict[str, float],
        strengths: list[str],
        weaknesses: list[str],
        skill_gaps: list[str],
        **kwargs
    ) -> str:
        """Save skill assessment results."""
        self._ensure_repositories()
        
        assessment_data = {
            "assessment_id": f"assessment_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "skill_category": skill_category,
            "overall_score": overall_score,
            "skill_scores": skill_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skill_gaps": skill_gaps,
            "assessed_at": datetime.utcnow(),
            **kwargs
        }
        
        return await self._assessment_repo.save_assessment(assessment_data)
    
    async def get_user_assessments(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all skill assessments for a user."""
        self._ensure_repositories()
        return await self._assessment_repo.get_user_assessments(user_id, limit)
    
    # ==================== Internship Recommendation Operations ====================
    
    async def save_internship_recommendations(
        self,
        user_id: str,
        recommendations: list[dict[str, Any]]
    ) -> list[str]:
        """Save internship recommendations."""
        self._ensure_repositories()
        
        # Add user_id and recommendation_id to each recommendation
        for rec in recommendations:
            if "recommendation_id" not in rec:
                rec["recommendation_id"] = f"internship_{uuid.uuid4().hex[:12]}"
            rec["user_id"] = user_id
            if "generated_at" not in rec:
                rec["generated_at"] = datetime.utcnow()
        
        return await self._internship_repo.save_recommendations(recommendations)
    
    async def get_user_internship_recommendations(
        self,
        user_id: str,
        limit: int = 20
    ) -> list[dict]:
        """Get internship recommendations for a user."""
        self._ensure_repositories()
        return await self._internship_repo.get_user_recommendations(user_id, limit)
    
    async def mark_internship_applied(self, recommendation_id: str) -> bool:
        """Mark an internship as applied."""
        self._ensure_repositories()
        return await self._internship_repo.mark_applied(recommendation_id)


# Global service instance
persistence_service = PersistenceService()
