"""
nlp/context/manager.py — Semantic Conversation State Manager

Enhanced to maintain structured state across the full conversation:
- Accumulated signals (weighted rolling average)
- Mentioned entities (colleges, branches, constraints)
- Sentiment trend tracking
- Contradiction detection
- Compact context summaries for LLM prompts

Persistence: Redis (if available) with 2-hour TTL, else in-memory.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

MAX_HISTORY_TURNS = 10
STATE_TTL_SECONDS = 7200  # 2 hours
CONTRADICTION_THRESHOLD = 0.4  # Signal difference > 0.4 triggers contradiction
SIGNAL_WEIGHT_NEW = 0.3  # Weight for new signal in rolling average
SIGNAL_WEIGHT_OLD = 0.7  # Weight for old signal in rolling average

# ── Conversation State Data Model ────────────────────────────────────────────

@dataclass
class ExpressedConstraints:
    """Constraints mentioned by the student."""
    budget_lakh: Optional[float] = None
    location: Optional[str] = None
    exam_type: Optional[str] = None
    rank: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ConversationState:
    """
    Structured semantic state maintained across the full conversation.
    
    Attributes:
        session_id: Unique session identifier
        accumulated_signals: Running weighted average of all extracted signals
        mentioned_colleges: Colleges mentioned by student across all turns
        mentioned_branches: Branches discussed
        sentiment_trend: Per-turn compound sentiment (tracks mood changes)
        expressed_constraints: Budget, location, exam type, rank
        open_questions: Questions student hasn't answered yet
        contradictions: Detected contradictions (e.g., "loves math" → "hates math")
        history: Recent conversation turns (limited to MAX_HISTORY_TURNS)
        last_intent: Most recent detected intent
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    """
    session_id: str
    accumulated_signals: dict[str, float] = field(default_factory=dict)
    mentioned_colleges: list[str] = field(default_factory=list)
    mentioned_branches: list[str] = field(default_factory=list)
    sentiment_trend: list[float] = field(default_factory=list)
    expressed_constraints: ExpressedConstraints = field(default_factory=ExpressedConstraints)
    open_questions: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    last_intent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data['expressed_constraints'] = self.expressed_constraints.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> ConversationState:
        """Reconstruct from dict."""
        constraints_data = data.pop('expressed_constraints', {})
        constraints = ExpressedConstraints(**constraints_data)
        return cls(expressed_constraints=constraints, **data)


# ── Context Manager ───────────────────────────────────────────────────────────

class ContextManager:
    """
    Manages semantic conversation state with persistence.
    
    Features:
    - Weighted rolling average for accumulated signals
    - Contradiction detection
    - Compact context summaries for LLM prompts
    - Redis persistence (with in-memory fallback)
    """
    
    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize context manager.
        
        Args:
            redis_client: Optional Redis client for persistence.
                         If None, uses in-memory storage.
        """
        self._redis = redis_client
        self._memory_store: dict[str, ConversationState] = {}
        
        if self._redis:
            logger.info("ContextManager initialized with Redis persistence")
        else:
            logger.info("ContextManager initialized with in-memory storage")
    
    def _get_state(self, session_id: str) -> ConversationState:
        """
        Retrieve conversation state from storage.
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationState (creates new if not found)
        """
        # Try Redis first
        if self._redis:
            try:
                key = f"conversation_state:{session_id}"
                data = self._redis.get(key)
                if data:
                    state_dict = json.loads(data)
                    return ConversationState.from_dict(state_dict)
            except Exception as e:
                logger.warning(f"Redis get failed for {session_id}: {e}")
        
        # Fallback to memory
        if session_id in self._memory_store:
            return self._memory_store[session_id]
        
        # Create new state
        return ConversationState(session_id=session_id)
    
    def _save_state(self, state: ConversationState) -> None:
        """
        Save conversation state to storage.
        
        Args:
            state: ConversationState to save
        """
        state.updated_at = datetime.utcnow().isoformat()
        
        # Save to Redis
        if self._redis:
            try:
                key = f"conversation_state:{state.session_id}"
                data = json.dumps(state.to_dict())
                self._redis.setex(key, STATE_TTL_SECONDS, data)
            except Exception as e:
                logger.warning(f"Redis save failed for {state.session_id}: {e}")
        
        # Always save to memory as backup
        self._memory_store[state.session_id] = state
    
    def update_signals(
        self,
        session_id: str,
        new_signals: dict[str, float],
    ) -> dict[str, str]:
        """
        Update accumulated signals with weighted rolling average.
        
        Formula: new_value = 0.7 * old_value + 0.3 * new_extraction
        
        Args:
            session_id: Session identifier
            new_signals: Newly extracted signals
        
        Returns:
            Dict of detected contradictions {dimension: message}
        """
        state = self._get_state(session_id)
        contradictions = {}
        
        for dimension, new_value in new_signals.items():
            old_value = state.accumulated_signals.get(dimension)
            
            if old_value is not None:
                # Check for contradiction
                diff = abs(new_value - old_value)
                if diff > CONTRADICTION_THRESHOLD:
                    contradiction_msg = (
                        f"{dimension.replace('_', ' ')}: "
                        f"Earlier {old_value:.2f}, now {new_value:.2f} "
                        f"(difference: {diff:.2f})"
                    )
                    contradictions[dimension] = contradiction_msg
                    state.contradictions.append(contradiction_msg)
                    logger.info(f"Contradiction detected in {session_id}: {contradiction_msg}")
                
                # Weighted rolling average
                updated_value = SIGNAL_WEIGHT_OLD * old_value + SIGNAL_WEIGHT_NEW * new_value
                state.accumulated_signals[dimension] = round(updated_value, 4)
            else:
                # First time seeing this dimension
                state.accumulated_signals[dimension] = round(new_value, 4)
        
        self._save_state(state)
        return contradictions
    
    def update_entities(
        self,
        session_id: str,
        entities: dict[str, Any],
    ) -> None:
        """
        Update mentioned entities (colleges, branches, constraints).
        
        Args:
            session_id: Session identifier
            entities: Extracted entities dict
        """
        state = self._get_state(session_id)
        
        # Update colleges
        for college in entities.get('colleges', []):
            if college not in state.mentioned_colleges:
                state.mentioned_colleges.append(college)
        
        # Update branches
        for branch in entities.get('branches', []):
            if branch not in state.mentioned_branches:
                state.mentioned_branches.append(branch)
        
        # Update constraints
        if 'budget_lakh' in entities and entities['budget_lakh']:
            state.expressed_constraints.budget_lakh = entities['budget_lakh']
        
        if 'locations' in entities and entities['locations']:
            # Take the first location mentioned
            state.expressed_constraints.location = entities['locations'][0]
        
        if 'exams' in entities and entities['exams']:
            # Take the first exam mentioned
            state.expressed_constraints.exam_type = entities['exams'][0]
        
        if 'ranks' in entities and entities['ranks']:
            # Take the first rank mentioned
            state.expressed_constraints.rank = entities['ranks'][0]
        
        self._save_state(state)
    
    def update_sentiment(
        self,
        session_id: str,
        sentiment_compound: float,
    ) -> None:
        """
        Add sentiment score to trend tracking.
        
        Args:
            session_id: Session identifier
            sentiment_compound: Compound sentiment score [-1, 1]
        """
        state = self._get_state(session_id)
        state.sentiment_trend.append(round(sentiment_compound, 3))
        
        # Keep only last 20 turns
        if len(state.sentiment_trend) > 20:
            state.sentiment_trend = state.sentiment_trend[-20:]
        
        self._save_state(state)
    
    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> None:
        """
        Add a conversation turn to history.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response (optional)
            intent: Detected intent (optional)
        """
        state = self._get_state(session_id)
        
        # Add user turn
        turn = {
            "role": "user",
            "message": user_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if intent:
            turn["intent"] = intent
            state.last_intent = intent
        
        state.history.append(turn)
        
        # Add assistant turn
        if assistant_message:
            state.history.append({
                "role": "assistant",
                "message": assistant_message,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Trim history to MAX_HISTORY_TURNS
        if len(state.history) > MAX_HISTORY_TURNS * 2:
            state.history = state.history[-(MAX_HISTORY_TURNS * 2):]
        
        self._save_state(state)
    
    def add_open_question(
        self,
        session_id: str,
        question: str,
    ) -> None:
        """
        Add a question that the student hasn't answered yet.
        
        Args:
            session_id: Session identifier
            question: Question text
        """
        state = self._get_state(session_id)
        if question not in state.open_questions:
            state.open_questions.append(question)
        self._save_state(state)
    
    def remove_open_question(
        self,
        session_id: str,
        question: str,
    ) -> None:
        """
        Remove a question that has been answered.
        
        Args:
            session_id: Session identifier
            question: Question text
        """
        state = self._get_state(session_id)
        if question in state.open_questions:
            state.open_questions.remove(question)
        self._save_state(state)
    
    def get_groq_context_summary(self, session_id: str) -> str:
        """
        Build a compact context summary for Groq (max 400 tokens ≈ 1600 chars).
        
        This replaces passing raw conversation history to save tokens.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Formatted context summary string
        """
        state = self._get_state(session_id)
        
        lines = []
        
        # 1. Accumulated signals (top 5 by value)
        if state.accumulated_signals:
            sorted_signals = sorted(
                state.accumulated_signals.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            signal_strs = [f"{dim.replace('_', ' ')}: {val:.2f}" for dim, val in sorted_signals]
            lines.append(f"Signals: {', '.join(signal_strs)}")
        
        # 2. Expressed constraints
        constraints = state.expressed_constraints.to_dict()
        if constraints:
            constraint_strs = []
            if 'budget_lakh' in constraints:
                constraint_strs.append(f"Budget: ₹{constraints['budget_lakh']}L")
            if 'location' in constraints:
                constraint_strs.append(f"Location: {constraints['location']}")
            if 'exam_type' in constraints:
                constraint_strs.append(f"Exam: {constraints['exam_type']}")
            if 'rank' in constraints:
                constraint_strs.append(f"Rank: {constraints['rank']}")
            lines.append(f"Constraints: {', '.join(constraint_strs)}")
        
        # 3. Mentioned entities
        if state.mentioned_colleges:
            colleges_str = ', '.join(state.mentioned_colleges[:3])
            if len(state.mentioned_colleges) > 3:
                colleges_str += f" (+{len(state.mentioned_colleges) - 3} more)"
            lines.append(f"Colleges: {colleges_str}")
        
        if state.mentioned_branches:
            branches_str = ', '.join(state.mentioned_branches[:3])
            lines.append(f"Branches: {branches_str}")
        
        # 4. Sentiment trend (last 5 turns)
        if state.sentiment_trend:
            recent_sentiment = state.sentiment_trend[-5:]
            avg_sentiment = sum(recent_sentiment) / len(recent_sentiment)
            trend = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            lines.append(f"Mood: {trend} (avg: {avg_sentiment:+.2f})")
        
        # 5. Contradictions (most recent 2)
        if state.contradictions:
            recent_contradictions = state.contradictions[-2:]
            lines.append(f"⚠️ Contradictions: {'; '.join(recent_contradictions)}")
        
        # 6. Open questions (max 2)
        if state.open_questions:
            open_q = state.open_questions[:2]
            lines.append(f"Unanswered: {'; '.join(open_q)}")
        
        # 7. Recent history (last 3 turns)
        if state.history:
            recent_history = state.history[-6:]  # Last 3 user+assistant pairs
            history_lines = []
            for turn in recent_history:
                role = turn['role'].capitalize()
                msg = turn['message'][:80]  # Truncate long messages
                history_lines.append(f"{role}: {msg}")
            lines.append(f"Recent:\n  " + "\n  ".join(history_lines))
        
        summary = "\n".join(lines)
        
        # Ensure we're under 1600 chars (≈400 tokens)
        if len(summary) > 1600:
            summary = summary[:1597] + "..."
        
        return summary
    
    def get(self, session_id: str) -> ConversationState:
        """
        Get full conversation state.
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationState
        """
        return self._get_state(session_id)
    
    def get_history_text(self, session_id: str, max_turns: int = 5) -> str:
        """
        Get conversation history as formatted text.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of turns to include
        
        Returns:
            Formatted history string
        """
        state = self._get_state(session_id)
        recent = state.history[-(max_turns * 2):]
        return "\n".join(
            f"{turn['role'].capitalize()}: {turn['message']}"
            for turn in recent
        )
    
    def clear(self, session_id: str) -> None:
        """
        Clear conversation state for a session.
        
        Args:
            session_id: Session identifier
        """
        # Clear from Redis
        if self._redis:
            try:
                key = f"conversation_state:{session_id}"
                self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed for {session_id}: {e}")
        
        # Clear from memory
        if session_id in self._memory_store:
            del self._memory_store[session_id]
    
    def list_sessions(self) -> list[str]:
        """
        List all active session IDs.
        
        Returns:
            List of session IDs
        """
        # From memory
        memory_sessions = set(self._memory_store.keys())
        
        # From Redis (if available)
        redis_sessions = set()
        if self._redis:
            try:
                pattern = "conversation_state:*"
                keys = self._redis.keys(pattern)
                redis_sessions = {key.decode().split(':', 1)[1] for key in keys}
            except Exception as e:
                logger.warning(f"Redis keys scan failed: {e}")
        
        return list(memory_sessions | redis_sessions)
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions from memory.
        
        Redis handles expiration automatically via TTL.
        This only cleans up memory store.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired = []
        
        for session_id, state in self._memory_store.items():
            updated_at = datetime.fromisoformat(state.updated_at)
            age = (now - updated_at).total_seconds()
            
            if age > STATE_TTL_SECONDS:
                expired.append(session_id)
        
        for session_id in expired:
            del self._memory_store[session_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions from memory")
        
        return len(expired)
