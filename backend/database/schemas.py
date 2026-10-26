"""
MongoDB document schemas for Pathfinder AI Career Counselor.
Defines the structure of documents stored in each collection.
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr


class UserProfile(BaseModel):
    """User profile schema for MongoDB storage."""
    user_id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    skills: list[str] = Field(default_factory=list)
    career_goals: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional fields from counseling session
    jee_rank: Optional[int] = None
    budget_lakh: Optional[float] = None
    preferred_location: Optional[str] = None
    exam_type: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "name": "John Doe",
                "email": "john@example.com",
                "college": "IIT Bombay",
                "branch": "CS",
                "cgpa": 8.5,
                "skills": ["Python", "Machine Learning", "Data Structures"],
                "career_goals": "Software Engineer at top tech company",
                "jee_rank": 1500,
                "budget_lakh": 5.0,
                "preferred_location": "South India"
            }
        }


class ChatMessage(BaseModel):
    """Chat message schema for conversation history."""
    chat_id: str = Field(..., description="Unique chat message identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Counseling session identifier")
    question: str = Field(..., description="Question asked by the AI")
    answer: str = Field(..., description="User's response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional context
    branch_scores: Optional[dict[str, float]] = None
    confidence: Optional[float] = None
    category: Optional[str] = None
    
    # LLM-powered adaptive engine: snapshot of student model after this turn
    student_model_snapshot: Optional[dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat_123",
                "user_id": "user_123",
                "session_id": "session_456",
                "question": "What subjects do you enjoy most?",
                "answer": "I love computer science and programming",
                "branch_scores": {"CS": 0.8, "Electronics": 0.6},
                "confidence": 0.75,
                "category": "interest_assessment",
                "student_model_snapshot": {
                    "math_aptitude": 0.6,
                    "logical_thinking": 0.7,
                    "hands_on": 0.3
                }
            }
        }


class ResumeAnalysis(BaseModel):
    """Resume analysis schema for storing parsed resume data."""
    resume_id: str = Field(..., description="Unique resume identifier")
    user_id: str = Field(..., description="User identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    
    # Parsed data
    extracted_text: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    
    # ATS scores
    ats_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    keyword_match_score: Optional[float] = None
    formatting_score: Optional[float] = None
    
    # AI feedback
    ai_feedback: Optional[str] = None
    recommendations: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_id": "resume_123",
                "user_id": "user_123",
                "filename": "john_resume.pdf",
                "file_size": 245760,
                "skills": ["Python", "Java", "React"],
                "ats_score": 85.5,
                "ai_feedback": "Strong technical background with relevant projects",
                "recommendations": ["Add more quantifiable achievements", "Include specific technologies used"]
            }
        }


class LearningRoadmap(BaseModel):
    """Learning roadmap schema for career path planning."""
    roadmap_id: str = Field(..., description="Unique roadmap identifier")
    user_id: str = Field(..., description="User identifier")
    target_role: str = Field(..., description="Target career role")
    current_level: str = Field(..., description="Current skill level")
    
    # Roadmap content
    milestones: list[dict[str, Any]] = Field(default_factory=list)
    timeline_weeks: int = Field(..., description="Estimated timeline in weeks")
    resources: list[dict[str, str]] = Field(default_factory=list)
    skills_to_learn: list[str] = Field(default_factory=list)
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    completed_milestones: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "roadmap_id": "roadmap_123",
                "user_id": "user_123",
                "target_role": "Full Stack Developer",
                "current_level": "Beginner",
                "timeline_weeks": 24,
                "skills_to_learn": ["React", "Node.js", "MongoDB", "AWS"],
                "progress_percentage": 25.0
            }
        }


class SkillAssessment(BaseModel):
    """Skill assessment schema for tracking skill evaluations."""
    assessment_id: str = Field(..., description="Unique assessment identifier")
    user_id: str = Field(..., description="User identifier")
    skill_category: str = Field(..., description="Category of skills assessed")
    
    # Assessment results
    overall_score: float = Field(..., ge=0.0, le=100.0)
    skill_scores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    
    # Gap analysis
    skill_gaps: list[str] = Field(default_factory=list)
    recommended_learning_paths: list[str] = Field(default_factory=list)
    estimated_learning_time_weeks: Optional[int] = None
    
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "assessment_id": "assessment_123",
                "user_id": "user_123",
                "skill_category": "Backend Development",
                "overall_score": 72.5,
                "skill_scores": {"Python": 85, "Django": 65, "SQL": 70},
                "strengths": ["Python programming", "Problem solving"],
                "weaknesses": ["System design", "Scalability"],
                "skill_gaps": ["Microservices", "Docker", "Kubernetes"]
            }
        }


class InternshipRecommendation(BaseModel):
    """Internship recommendation schema."""
    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Recommendation details
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Position/role title")
    location: str = Field(..., description="Location")
    duration: str = Field(..., description="Duration (e.g., '3 months')")
    stipend: Optional[str] = None
    
    # Match score
    match_score: float = Field(..., ge=0.0, le=100.0, description="How well it matches user profile")
    match_reasons: list[str] = Field(default_factory=list)
    
    # Requirements
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    
    # Application info
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    is_applied: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "internship_123",
                "user_id": "user_123",
                "company": "Google",
                "position": "Software Engineering Intern",
                "location": "Bangalore",
                "duration": "3 months",
                "stipend": "₹80,000/month",
                "match_score": 88.5,
                "match_reasons": ["Strong Python skills", "Relevant project experience"],
                "required_skills": ["Python", "Data Structures", "Algorithms"]
            }
        }
