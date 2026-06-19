"""
Repository layer for MongoDB operations.
Provides clean abstraction for database CRUD operations.
"""
import logging
from datetime import datetime
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import (
    UserProfile,
    ChatMessage,
    ResumeAnalysis,
    LearningRoadmap,
    SkillAssessment,
    InternshipRecommendation
)

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user profile operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users
    
    async def create_user(self, user_data: dict[str, Any]) -> str:
        """Create a new user profile."""
        try:
            user_profile = UserProfile(**user_data)
            result = await self.collection.insert_one(user_profile.dict())
            logger.info(f"✅ Created user: {user_profile.user_id}")
            return user_profile.user_id
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user profile by user_id."""
        try:
            user = await self.collection.find_one({"user_id": user_id})
            if user:
                user.pop("_id", None)  # Remove MongoDB internal ID
            return user
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user profile by email."""
        try:
            user = await self.collection.find_one({"email": email})
            if user:
                user.pop("_id", None)
            return user
        except Exception as e:
            logger.error(f"❌ Failed to get user by email {email}: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: dict[str, Any]) -> bool:
        """Update user profile."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                logger.info(f"✅ Updated user: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update user {user_id}: {e}")
            return False
    
    async def upsert_user(self, user_data: dict[str, Any]) -> str:
        """Create or update user profile."""
        user_id = user_data.get("user_id")
        existing_user = await self.get_user(user_id)
        
        if existing_user:
            await self.update_user(user_id, user_data)
        else:
            await self.create_user(user_data)
        
        return user_id


class ChatRepository:
    """Repository for chat history operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.chats
    
    async def save_chat_message(self, chat_data: dict[str, Any]) -> str:
        """Save a chat message."""
        try:
            chat_message = ChatMessage(**chat_data)
            await self.collection.insert_one(chat_message.dict())
            logger.info(f"✅ Saved chat message: {chat_message.chat_id}")
            return chat_message.chat_id
        except Exception as e:
            logger.error(f"❌ Failed to save chat message: {e}")
            raise
    
    async def get_chat_history(self, user_id: str, session_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Get chat history for a user."""
        try:
            query = {"user_id": user_id}
            if session_id:
                query["session_id"] = session_id
            
            cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
            messages = await cursor.to_list(length=limit)
            
            # Remove MongoDB internal IDs
            for msg in messages:
                msg.pop("_id", None)
            
            return messages
        except Exception as e:
            logger.error(f"❌ Failed to get chat history: {e}")
            return []
    
    async def get_session_history(self, session_id: str) -> list[dict]:
        """Get all messages for a specific session."""
        try:
            cursor = self.collection.find({"session_id": session_id}).sort("timestamp", 1)
            messages = await cursor.to_list(length=None)
            
            for msg in messages:
                msg.pop("_id", None)
            
            return messages
        except Exception as e:
            logger.error(f"❌ Failed to get session history: {e}")
            return []


class ResumeRepository:
    """Repository for resume analysis operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.resumes
    
    async def save_resume(self, resume_data: dict[str, Any]) -> str:
        """Save resume analysis."""
        try:
            resume = ResumeAnalysis(**resume_data)
            await self.collection.insert_one(resume.dict())
            logger.info(f"✅ Saved resume: {resume.resume_id}")
            return resume.resume_id
        except Exception as e:
            logger.error(f"❌ Failed to save resume: {e}")
            raise
    
    async def get_user_resumes(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all resumes for a user."""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("uploaded_at", -1).limit(limit)
            resumes = await cursor.to_list(length=limit)
            
            for resume in resumes:
                resume.pop("_id", None)
            
            return resumes
        except Exception as e:
            logger.error(f"❌ Failed to get resumes: {e}")
            return []
    
    async def get_resume(self, resume_id: str) -> Optional[dict]:
        """Get a specific resume."""
        try:
            resume = await self.collection.find_one({"resume_id": resume_id})
            if resume:
                resume.pop("_id", None)
            return resume
        except Exception as e:
            logger.error(f"❌ Failed to get resume: {e}")
            return None


class RoadmapRepository:
    """Repository for learning roadmap operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.roadmaps
    
    async def save_roadmap(self, roadmap_data: dict[str, Any]) -> str:
        """Save a learning roadmap."""
        try:
            roadmap = LearningRoadmap(**roadmap_data)
            await self.collection.insert_one(roadmap.dict())
            logger.info(f"✅ Saved roadmap: {roadmap.roadmap_id}")
            return roadmap.roadmap_id
        except Exception as e:
            logger.error(f"❌ Failed to save roadmap: {e}")
            raise
    
    async def get_user_roadmaps(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all roadmaps for a user."""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            roadmaps = await cursor.to_list(length=limit)
            
            for roadmap in roadmaps:
                roadmap.pop("_id", None)
            
            return roadmaps
        except Exception as e:
            logger.error(f"❌ Failed to get roadmaps: {e}")
            return []
    
    async def update_roadmap_progress(self, roadmap_id: str, progress_data: dict[str, Any]) -> bool:
        """Update roadmap progress."""
        try:
            progress_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"roadmap_id": roadmap_id},
                {"$set": progress_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update roadmap progress: {e}")
            return False


class SkillAssessmentRepository:
    """Repository for skill assessment operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.skill_assessments
    
    async def save_assessment(self, assessment_data: dict[str, Any]) -> str:
        """Save a skill assessment."""
        try:
            assessment = SkillAssessment(**assessment_data)
            await self.collection.insert_one(assessment.dict())
            logger.info(f"✅ Saved assessment: {assessment.assessment_id}")
            return assessment.assessment_id
        except Exception as e:
            logger.error(f"❌ Failed to save assessment: {e}")
            raise
    
    async def get_user_assessments(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all assessments for a user."""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("assessed_at", -1).limit(limit)
            assessments = await cursor.to_list(length=limit)
            
            for assessment in assessments:
                assessment.pop("_id", None)
            
            return assessments
        except Exception as e:
            logger.error(f"❌ Failed to get assessments: {e}")
            return []


class InternshipRepository:
    """Repository for internship recommendation operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.internship_recommendations
    
    async def save_recommendations(self, recommendations: list[dict[str, Any]]) -> list[str]:
        """Save multiple internship recommendations."""
        try:
            recommendation_ids = []
            for rec_data in recommendations:
                rec = InternshipRecommendation(**rec_data)
                await self.collection.insert_one(rec.dict())
                recommendation_ids.append(rec.recommendation_id)
            
            logger.info(f"✅ Saved {len(recommendation_ids)} internship recommendations")
            return recommendation_ids
        except Exception as e:
            logger.error(f"❌ Failed to save recommendations: {e}")
            raise
    
    async def get_user_recommendations(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get internship recommendations for a user."""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("match_score", -1).limit(limit)
            recommendations = await cursor.to_list(length=limit)
            
            for rec in recommendations:
                rec.pop("_id", None)
            
            return recommendations
        except Exception as e:
            logger.error(f"❌ Failed to get recommendations: {e}")
            return []
    
    async def mark_applied(self, recommendation_id: str) -> bool:
        """Mark an internship as applied."""
        try:
            result = await self.collection.update_one(
                {"recommendation_id": recommendation_id},
                {"$set": {"is_applied": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to mark as applied: {e}")
            return False
