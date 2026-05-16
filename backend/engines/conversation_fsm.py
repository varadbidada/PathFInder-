"""
engines/conversation_fsm.py — Finite State Machine for Conversation Flow

REFACTORED ARCHITECTURE:
- Structured state (NO message history dependency)
- Signal-based intelligence
- Deterministic scoring
- Message-independent predictions
"""
from __future__ import annotations
import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationStage(str, Enum):
    """Conversation stages in order"""
    INTRODUCTION = "introduction"
    INTEREST_ASSESSMENT = "interest_assessment"
    SKILL_ASSESSMENT = "skill_assessment"
    WORKSTYLE_ASSESSMENT = "workstyle_assessment"
    TIE_BREAKER = "tie_breaker"
    BRANCH_PREDICTION = "branch_prediction"
    COLLEGE_PREDICTION = "college_prediction"
    FINAL_SUMMARY = "final_summary"


# Stage progression order
STAGE_ORDER = [
    ConversationStage.INTRODUCTION,
    ConversationStage.INTEREST_ASSESSMENT,
    ConversationStage.SKILL_ASSESSMENT,
    ConversationStage.WORKSTYLE_ASSESSMENT,
    ConversationStage.BRANCH_PREDICTION,
    ConversationStage.COLLEGE_PREDICTION,
    ConversationStage.FINAL_SUMMARY,
]


@dataclass
class ConversationState:
    """
    Structured conversation state - COMPLETELY INDEPENDENT of chat messages.
    
    CRITICAL ARCHITECTURE PRINCIPLE:
    ═══════════════════════════════════════════════════════════════════════════
    This state is the SINGLE SOURCE OF TRUTH for ALL intelligence:
    - Branch scoring
    - Question progression
    - Stage transitions
    - Confidence calculation
    
    Chat messages are DISPLAY ONLY and NEVER used for predictions.
    ═══════════════════════════════════════════════════════════════════════════
    """
    session_id: str
    
    # ── STRUCTURED SIGNALS (Single Source of Truth) ──────────────────────────
    accumulated_signals: Dict[str, float] = field(default_factory=dict)
    signal_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # ── BRANCH SCORING STATE ──────────────────────────────────────────────────
    branch_scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    top_branch: Optional[str] = None
    confidence_gap: float = 0.0
    
    # ── QUESTION TRACKING ─────────────────────────────────────────────────────
    current_stage: ConversationStage = ConversationStage.INTRODUCTION
    questions_asked: List[str] = field(default_factory=list)
    questions_text: List[str] = field(default_factory=list)
    total_questions: int = 0
    
    # ── STAGE PROGRESSION ─────────────────────────────────────────────────────
    completed_stages: List[ConversationStage] = field(default_factory=list)
    stage_transitions: List[Dict[str, Any]] = field(default_factory=list)
    tie_breaker_count: int = 0
    
    # ── USER METADATA ─────────────────────────────────────────────────────────
    rank: Optional[int] = None
    exam_type: str = "jee_main"
    budget_lakh: Optional[float] = None
    preferred_location: Optional[str] = None
    
    # ── TIMESTAMPS ────────────────────────────────────────────────────────────
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # ══════════════════════════════════════════════════════════════════════════
    # SIGNAL MANAGEMENT (Core Intelligence)
    # ══════════════════════════════════════════════════════════════════════════
    
    def update_signals(self, new_signals: Dict[str, float], question_id: str) -> None:
        """
        Update accumulated signals with new data using exponential moving average.
        
        CRITICAL: This is the ONLY method that updates intelligence state.
        EMA gives more weight to recent responses (alpha=0.35).
        """
        logger.info(f"[SIGNAL] Updating signals for question: {question_id}")
        
        # Track signal history for audit trail
        self.signal_history.append({
            "question_id": question_id,
            "signals": new_signals.copy(),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Exponential moving average: newer answers have more influence
        alpha = 0.35  # weight for newer responses, older responses decay
        
        for key, new_value in new_signals.items():
            if isinstance(new_value, (int, float)):
                if key in self.accumulated_signals:
                    # EMA: new_avg = old_avg * (1 - alpha) + new_value * alpha
                    self.accumulated_signals[key] = (
                        self.accumulated_signals[key] * (1 - alpha) + new_value * alpha
                    )
                else:
                    # First value for this signal
                    self.accumulated_signals[key] = new_value
        
        self.updated_at = datetime.utcnow()
        logger.info(f"[SIGNAL] EMA updated {len(self.accumulated_signals)} signal dimensions from {len(self.signal_history)} responses")
    
    def get_signals(self) -> Dict[str, float]:
        """Get current accumulated signals (read-only)"""
        return self.accumulated_signals.copy()
    
    # ══════════════════════════════════════════════════════════════════════════
    # BRANCH SCORING (Derived from Signals ONLY)
    # ══════════════════════════════════════════════════════════════════════════
    
    def update_branch_scores(self, scores: Dict[str, float], confidence: float) -> None:
        """
        Update branch scores and confidence.
        
        CRITICAL: Scores MUST ONLY be derived from accumulated_signals.
        NEVER from message history.
        """
        logger.info(f"[SCORING] Updating branch scores")
        
        self.branch_scores = scores.copy()
        self.confidence = confidence
        
        # Update derived fields
        if scores:
            self.top_branch = max(scores, key=scores.get)
            sorted_scores = sorted(scores.values(), reverse=True)
            self.confidence_gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) >= 2 else 1.0
        
        self.updated_at = datetime.utcnow()
        logger.info(f"[SCORING] Top branch: {self.top_branch} (gap: {self.confidence_gap:.3f})")
    
    def get_top_branch(self) -> Optional[str]:
        """Get the top scoring branch"""
        return self.top_branch
    
    def get_confidence_gap(self) -> float:
        """Get the gap between top 2 branches"""
        return self.confidence_gap
    
    # ══════════════════════════════════════════════════════════════════════════
    # QUESTION TRACKING (Prevents Duplicates)
    # ══════════════════════════════════════════════════════════════════════════
    
    def add_question(self, question_id: str, question_text: str) -> None:
        """Add a question to the asked list"""
        if question_id not in self.questions_asked:
            self.questions_asked.append(question_id)
            self.questions_text.append(question_text.lower())
            self.total_questions += 1
            self.updated_at = datetime.utcnow()
            logger.info(f"[QUESTION] Asked: {question_id} (total: {self.total_questions})")
    
    def has_asked_question(self, question_id: str) -> bool:
        """Check if question has been asked"""
        return question_id in self.questions_asked
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════
    
    def mark_stage_complete(self, stage: ConversationStage) -> None:
        """Mark a stage as completed"""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
            self.stage_transitions.append({
                "from": self.current_stage.value,
                "to": stage.value,
                "timestamp": datetime.utcnow().isoformat(),
            })
            logger.info(f"[STAGE] Completed: {stage.value}")
    
    def should_trigger_tie_breaker(self) -> bool:
        """Check if tie-breaker should be triggered"""
        if self.tie_breaker_count >= 3:
            return False
        return self.confidence_gap < 0.15
    
    def can_progress_to_next_stage(self) -> bool:
        """Check if we can move to next stage"""
        if self.current_stage == ConversationStage.INTRODUCTION:
            return True
        
        if self.current_stage == ConversationStage.TIE_BREAKER:
            return self.tie_breaker_count >= 3 or self.confidence_gap >= 0.15
        
        # Other stages need minimum questions
        min_questions_per_stage = {
            ConversationStage.INTEREST_ASSESSMENT: 2,
            ConversationStage.SKILL_ASSESSMENT: 2,
            ConversationStage.WORKSTYLE_ASSESSMENT: 2,
        }
        
        stage_prefix_map = {
            ConversationStage.INTEREST_ASSESSMENT: "interest_",
            ConversationStage.SKILL_ASSESSMENT: "skill_",
            ConversationStage.WORKSTYLE_ASSESSMENT: "workstyle_",
        }
        
        prefix = stage_prefix_map.get(self.current_stage, self.current_stage.value)
        stage_questions = sum(1 for qid in self.questions_asked if qid.startswith(prefix))
        min_required = min_questions_per_stage.get(self.current_stage, 1)
        
        return stage_questions >= min_required


class ConversationFSM:
    """Finite State Machine for conversation flow"""
    
    def __init__(self, state: ConversationState):
        self.state = state
    
    def get_next_stage(self) -> ConversationStage:
        """Determine the next stage based on current state"""
        current = self.state.current_stage
        
        if current == ConversationStage.TIE_BREAKER:
            if not self.state.should_trigger_tie_breaker() or self.state.tie_breaker_count >= 3:
                return ConversationStage.BRANCH_PREDICTION
            return ConversationStage.TIE_BREAKER
        
        if (current in [ConversationStage.INTEREST_ASSESSMENT,
                        ConversationStage.SKILL_ASSESSMENT,
                        ConversationStage.WORKSTYLE_ASSESSMENT] and
                self.state.should_trigger_tie_breaker() and
                ConversationStage.TIE_BREAKER not in self.state.completed_stages):
            return ConversationStage.TIE_BREAKER
        
        try:
            current_idx = STAGE_ORDER.index(current)
            if current_idx < len(STAGE_ORDER) - 1:
                return STAGE_ORDER[current_idx + 1]
        except ValueError:
            pass
        
        return ConversationStage.FINAL_SUMMARY
    
    def transition_to_stage(self, stage: ConversationStage) -> None:
        """Transition to a new stage"""
        old_stage = self.state.current_stage
        self.state.mark_stage_complete(old_stage)
        self.state.current_stage = stage
        logger.info(f"[STAGE] Transition: {old_stage.value} → {stage.value}")
    
    def should_progress(self) -> bool:
        """Check if we should progress to next stage"""
        return self.state.can_progress_to_next_stage()
    
    def progress_if_ready(self) -> bool:
        """Progress to next stage if ready"""
        if self.should_progress():
            next_stage = self.get_next_stage()
            if next_stage != self.state.current_stage:
                self.transition_to_stage(next_stage)
                return True
        return False
    
    def is_complete(self) -> bool:
        """Check if conversation is complete"""
        return self.state.current_stage == ConversationStage.FINAL_SUMMARY
    
    def get_stage_progress(self) -> Dict[str, Any]:
        """Get progress information"""
        return {
            "current_stage": self.state.current_stage.value,
            "completed_stages": [s.value for s in self.state.completed_stages],
            "total_questions": self.state.total_questions,
            "tie_breaker_count": self.state.tie_breaker_count,
            "confidence_gap": self.state.get_confidence_gap(),
            "top_branch": self.state.get_top_branch(),
        }


def semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity using word overlap"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def is_duplicate_question(question_text: str, asked_questions: List[str], threshold: float = 0.70) -> bool:
    """Check if a question is semantically similar to previously asked questions"""
    question_lower = question_text.lower()
    
    for asked in asked_questions:
        similarity = semantic_similarity(question_lower, asked)
        if similarity >= threshold:
            logger.warning(f"[QUESTION] Duplicate detected (similarity: {similarity:.2%})")
            return True
    
    return False
