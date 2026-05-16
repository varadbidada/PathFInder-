"""
engines/session_manager.py — Session State Manager

Manages persistent conversation state in memory (can be extended to Redis/DB).
"""
from __future__ import annotations
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from engines.conversation_fsm import ConversationState, ConversationStage

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions"""
    
    def __init__(self, ttl_hours: int = 2):
        self._sessions: Dict[str, ConversationState] = {}
        self.ttl_hours = ttl_hours
    
    def create_session(
        self,
        session_id: str,
        rank: Optional[int] = None,
        budget_lakh: Optional[float] = None,
        preferred_location: Optional[str] = None,
    ) -> ConversationState:
        """Create a new conversation session with complete isolation"""
        # Check if session already exists - force delete to prevent contamination
        if session_id in self._sessions:
            logger.warning(f"[RESTART] Session {session_id} already exists! Force deleting to prevent contamination.")
            self.delete_session(session_id)
        
        state = ConversationState(
            session_id=session_id,
            rank=rank,
            budget_lakh=budget_lakh,
            preferred_location=preferred_location,
        )
        
        self._sessions[session_id] = state
        logger.info(f"[SESSION_CREATE] New session: {session_id} | Active sessions: {len(self._sessions)}")
        
        return state
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get a session by ID"""
        session = self._sessions.get(session_id)
        
        if session:
            # Check if session has expired
            if datetime.utcnow() - session.updated_at > timedelta(hours=self.ttl_hours):
                logger.warning(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
        
        return session
    
    def update_session(self, state: ConversationState) -> None:
        """Update a session"""
        state.updated_at = datetime.utcnow()
        self._sessions[state.session_id] = state
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and log the destruction"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"[SESSION_DELETE] Session destroyed: {session_id} | Remaining sessions: {len(self._sessions)}")
            return True
        logger.warning(f"[SESSION_DELETE] Attempted to delete non-existent session: {session_id}")
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, state in self._sessions.items()
            if now - state.updated_at > timedelta(hours=self.ttl_hours)
        ]
        
        for sid in expired:
            self.delete_session(sid)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get session statistics"""
        state = self.get_session(session_id)
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "current_stage": state.current_stage.value,
            "total_questions": state.total_questions,
            "tie_breaker_count": state.tie_breaker_count,
            "completed_stages": [s.value for s in state.completed_stages],
            "branch_scores": state.branch_scores,
            "top_branch": state.get_top_branch(),
            "confidence_gap": state.get_confidence_gap(),
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
        }


# Global session manager instance
session_manager = SessionManager()
