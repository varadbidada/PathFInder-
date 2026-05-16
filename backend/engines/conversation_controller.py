"""
engines/conversation_controller.py — Conversation Controller

Orchestrates the conversation flow using FSM, question bank, and session management.
LLM is ONLY used for natural phrasing, NOT for flow control.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from engines.conversation_fsm import (
    ConversationState,
    ConversationFSM,
    ConversationStage,
    is_duplicate_question,
)
from engines.question_bank import question_bank, Question
from engines.session_manager import session_manager
from engines.rule_engine import evaluate
from services.ai_service import extract_signals

logger = logging.getLogger(__name__)


class ConversationController:
    """Main controller for conversation flow"""

    def __init__(self):
        self.question_bank = question_bank
        self.session_manager = session_manager

    async def start_conversation(
        self,
        session_id: str,
        rank: Optional[int] = None,
        budget_lakh: Optional[float] = None,
        preferred_location: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Start a new conversation.

        Returns:
            (question_id, question_text)
        """
        # Create session
        state = self.session_manager.create_session(
            session_id=session_id,
            rank=rank,
            budget_lakh=budget_lakh,
            preferred_location=preferred_location,
        )

        # Get introduction question
        question = self.question_bank.get_next_question(
            stage=ConversationStage.INTRODUCTION,
            asked_ids=[],
        )

        if question:
            state.add_question(question.id, question.text)
            self.session_manager.update_session(state)
            logger.info(f"Conversation started: {session_id}")
            return question.id, question.text

        return "", "Hi! I'm Pathfinder. Let's find your perfect engineering branch!"

    async def process_message(
        self,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Process a user message using STRUCTURED STATE ONLY.
        
        REFACTORED ARCHITECTURE:
        ═══════════════════════════════════════════════════════════════════════
        1. Extract signals from user answer
        2. Update structured state (NOT message history)
        3. Calculate scores from accumulated signals ONLY
        4. Return next question
        
        Messages are DISPLAY ONLY - never used for intelligence.
        ═══════════════════════════════════════════════════════════════════════
        """
        logger.info(f"[PROCESS] ========== PROCESSING NEW MESSAGE ==========")
        
        # Get session
        state = self.session_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        # Get current question ID for signal tracking
        current_question_id = state.questions_asked[-1] if state.questions_asked else "intro"
        
        # ── STEP 1: Extract signals from user answer ─────────────────────────
        logger.info(f"[PROCESS] Step 1: Extracting signals from answer")
        signals = await extract_signals(
            user_answer=user_message,
            question_asked=state.questions_text[-1] if state.questions_text else "",
            conversation_context="",  # NO CONTEXT - signals only from current answer
        )

        # Update exam_type if detected
        if hasattr(signals, "Exam_Type") and signals.Exam_Type != "unknown":
            if signals.Exam_Type in ["jee_main", "jee_advanced"]:
                state.exam_type = signals.Exam_Type
                logger.info(f"[PROCESS] Detected exam type: {signals.Exam_Type}")

        # ── STEP 2: Update structured state with new signals ─────────────────
        logger.info(f"[PROCESS] Step 2: Updating structured state")
        signal_dict = signals.to_dict()
        state.update_signals(signal_dict, current_question_id)

        # ── STEP 3: Calculate branch scores from accumulated signals ─────────
        logger.info(f"[PROCESS] Step 3: Calculating branch scores from signals")
        accumulated = state.get_signals()
        
        result = evaluate(
            accumulated,
            personality=getattr(signals, "Introvert_Extrovert", "ambivert"),
            risk_level=getattr(signals, "Risk_Level", "medium"),
        )
        
        logger.info(f"[PROCESS] Branch scores: {result.normalized_scores}")

        # ── STEP 4: Update branch scores in state ────────────────────────────
        state.update_branch_scores(result.normalized_scores, result.confidence)

        # ── STEP 5: Check stage progression ──────────────────────────────────
        fsm = ConversationFSM(state)
        progressed = fsm.progress_if_ready()
        if progressed:
            logger.info(f"[PROCESS] Progressed to stage: {state.current_stage.value}")

        # ── STEP 6: Check if conversation is complete ────────────────────────
        if fsm.is_complete():
            self.session_manager.update_session(state)
            return {
                "question_id": None,
                "question_text": None,
                "stage": state.current_stage.value,
                "branch_scores": state.branch_scores,
                "confidence": state.confidence,
                "is_complete": True,
                "top_branch": state.get_top_branch(),
                "confidence_gap": state.get_confidence_gap(),
            }

        # ── STEP 7: Get next question ────────────────────────────────────────
        # Try reactive generation first, fall back to question bank
        from services.ai_service import get_reactive_question
        
        # Build session_state for reactive question
        session_state = {
            "last_user_message": user_message,
            "last_question": state.questions_text[-1] if state.questions_text else "",
            "messages": [
                {"role": "assistant" if i % 2 == 0 else "user", "content": q}
                for i, q in enumerate(state.questions_text)
            ],
            "student_profile": {
                "branch_scores": state.branch_scores,
                "top_branch": state.get_top_branch(),
                "confidence": result.confidence,
            },
            "questions_text": state.questions_text,
        }
        
        # Try reactive generation with aggressive timeout
        used_reactive = False
        next_question_text = None
        question_id = None
        
        try:
            # Try reactive question with short timeout
            reactive_question = await asyncio.wait_for(
                get_reactive_question(session_state),
                timeout=8.0  # Very short timeout
            )
            if reactive_question and len(reactive_question) > 10:
                # Use reactive question
                question_id = f"reactive_{len(state.questions_asked)}"
                next_question_text = reactive_question
                used_reactive = True
                logger.info(f"[PROCESS] Using reactive question: {reactive_question[:50]}...")
            else:
                raise ValueError("Reactive question too short")
        except Exception as e:
            logger.warning(f"Reactive question failed quickly, falling back to bank: {e}")
            # Fall back to existing question bank logic
            next_question = self._get_next_question(state, fsm)
            if next_question:
                question_id = next_question.id
                next_question_text = next_question.text
                used_reactive = False
                logger.info(f"[PROCESS] Using question bank: {next_question_text[:50]}...")
            else:
                # Ultimate fallback - hardcoded questions
                fallback_questions = [
                    "What subjects or activities do you enjoy most? Tell me about your interests and hobbies.",
                    "Do you prefer working with your hands on practical projects, or do you enjoy theoretical problem-solving more?",
                    "When you think about your future career, do you see yourself working more with people or with technology?",
                    "What kind of problems excite you most - mathematical puzzles, creative challenges, or real-world engineering problems?",
                    "Are you more interested in building things, analyzing data, or helping people directly?"
                ]
                question_index = len(state.questions_asked) % len(fallback_questions)
                question_id = f"fallback_{question_index:03d}"
                next_question_text = fallback_questions[question_index]
                used_reactive = False
                logger.info(f"[PROCESS] Using fallback question: {next_question_text[:50]}...")

        if not next_question_text:
            fsm.transition_to_stage(ConversationStage.BRANCH_PREDICTION)
            self.session_manager.update_session(state)
            return {
                "question_id": None,
                "question_text": "I have enough information! Let me analyse your profile...",
                "stage": state.current_stage.value,
                "branch_scores": state.branch_scores,
                "confidence": state.confidence,
                "is_complete": False,
                "top_branch": state.get_top_branch(),
                "confidence_gap": state.get_confidence_gap(),
                "used_reactive": False,
            }

        # Record the question as asked
        state.add_question(question_id, next_question_text)

        # Persist session
        self.session_manager.update_session(state)

        logger.info(f"[PROCESS] ========== MESSAGE PROCESSING COMPLETE ==========")

        return {
            "question_id": question_id,
            "question_text": next_question_text,
            "stage": state.current_stage.value,
            "branch_scores": state.branch_scores,
            "confidence": state.confidence,
            "is_complete": False,
            "top_branch": state.get_top_branch(),
            "confidence_gap": state.get_confidence_gap(),
            "used_reactive": used_reactive,
        }

    def _get_next_question(
        self,
        state: ConversationState,
        fsm: ConversationFSM,
        _skip_ids: Optional[List[str]] = None,
    ) -> Optional[Question]:
        """
        Get the next question with duplicate detection.

        Uses an explicit skip list to avoid infinite recursion when semantic
        duplicates are encountered.  The tie-breaker counter is incremented
        only when a valid, non-duplicate question is found.

        Returns:
            Next question or None
        """
        if _skip_ids is None:
            _skip_ids = []

        current_stage = state.current_stage

        # Hard limit on tie-breaker questions
        if current_stage == ConversationStage.TIE_BREAKER and state.tie_breaker_count >= 3:
            logger.info("Tie-breaker limit reached, forcing completion")
            return None

        # Build full exclusion list: already asked + temporarily skipped this call
        excluded_ids = list(state.questions_asked) + _skip_ids

        # Ask the question bank for the best candidate (with session_id for randomization)
        question = self.question_bank.get_next_question(
            stage=current_stage,
            asked_ids=excluded_ids,
            branch_scores=state.branch_scores,
            session_id=state.session_id,
        )

        if not question:
            logger.info(f"No more questions for stage: {current_stage.value}")
            return None

        # Sanity check: must not already be in the asked list
        if state.has_asked_question(question.id):
            logger.warning(f"Question already asked (double-check failed): {question.id}")
            return None

        # Semantic duplicate check against all previously asked question texts
        if is_duplicate_question(question.text, state.questions_text, threshold=0.70):
            logger.warning(
                f"Semantically similar question detected: {question.id} — skipping"
            )
            _skip_ids.append(question.id)
            return self._get_next_question(state, fsm, _skip_ids=_skip_ids)

        # Increment tie-breaker counter only when we have a valid question to serve
        if current_stage == ConversationStage.TIE_BREAKER:
            state.tie_breaker_count += 1
            logger.info(
                f"Tie-breaker question #{state.tie_breaker_count}: {question.id}"
            )

        return question

    def get_session_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session progress information"""
        return self.session_manager.get_session_stats(session_id)

    def reset_session(self, session_id: str) -> bool:
        """Reset a session"""
        return self.session_manager.delete_session(session_id)


# Global controller instance
conversation_controller = ConversationController()
