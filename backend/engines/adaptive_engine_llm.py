"""
LLM-Powered Adaptive Question Engine for Class 12 Students.
Generates contextual questions based on growing student personality model.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from models.student_model import StudentModel
from services.counsellor_prompts import (
    SYSTEM_PROMPT,
    build_extraction_prompt,
    build_confirmation_prompt,
    get_branch_description,
    build_fallback_question,
    build_retry_prompt
)

logger = logging.getLogger(__name__)


class LLMAdaptiveEngine:
    """
    Adaptive question engine that uses LLM to generate contextual questions
    for Class 12 students with zero engineering background.
    """
    
    def __init__(self, questions_file: str = "data/questions_class12.json"):
        """Initialize engine with Class 12 friendly questions."""
        self.questions_file = Path(__file__).parent.parent / questions_file
        self.opener_questions = []
        self.stage_templates = {}
        self.branch_profiles = {}
        
        self._load_questions()
    
    def _load_questions(self):
        """Load opener questions and stage templates."""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.opener_questions = data.get('opener_questions', [])
                self.stage_templates = data.get('stage_templates', {})
                self.branch_profiles = data.get('branch_profiles', {})
                logger.info(f"✅ Loaded {len(self.opener_questions)} opener questions")
        except Exception as e:
            logger.error(f"❌ Failed to load questions: {e}")
            # Fallback to hardcoded openers
            self.opener_questions = [
                {
                    "id": "q_opener_1",
                    "text": "If you had a completely free Saturday with no phone and no plans, what would you most likely end up doing?",
                    "stage": "personality",
                    "fixed": True
                },
                {
                    "id": "q_opener_2",
                    "text": "In school, which subject made you feel like time was flying when you were deep in it?",
                    "stage": "personality",
                    "fixed": True
                },
                {
                    "id": "q_opener_3",
                    "text": "When you picture yourself 10 years from now — not what you think you should say, but what actually excites you — what are you doing?",
                    "stage": "personality",
                    "fixed": True
                }
            ]
    
    def create_session(
        self,
        exam_type: str = "jee_main",
        rank: Optional[int] = None,
        budget_lakh: Optional[float] = None,
        preferred_location: Optional[str] = None,
        max_questions: int = 10
    ) -> dict[str, Any]:
        """Create a new counseling session with StudentModel."""
        return {
            "exam_type": exam_type,
            "rank": rank,
            "budget_lakh": budget_lakh,
            "preferred_location": preferred_location,
            "max_questions": max_questions,
            "student_model": StudentModel(),
            "questions_asked": [],
            "answers_given": [],
            "current_stage": "personality",
            "turn_number": 0,
            "is_complete": False,
            "llm_enabled": True  # flag to use LLM or fallback
        }
    
    def select_opening_question(self, session: dict[str, Any]) -> dict[str, Any]:
        """Return first fixed opener question."""
        if not self.opener_questions:
            return {
                "text": "Tell me about yourself and what interests you.",
                "type": "open",
                "stage": "personality"
            }
        
        return {
            "text": self.opener_questions[0]["text"],
            "id": self.opener_questions[0]["id"],
            "type": "open",
            "stage": "personality"
        }
    
    def process_answer(
        self,
        session: dict[str, Any],
        user_answer: str,
        llm_client = None
    ) -> dict[str, Any]:
        """
        Process student answer and generate next question using LLM.
        
        The LLM keeps generating questions until ALL traits are adequately measured.
        
        Args:
            session: Current session state
            user_answer: Student's answer text
            llm_client: LLM client for generating questions
        
        Returns:
            Dict with next question, student model updates, and completion status
        """
        turn = session["turn_number"]
        student_model: StudentModel = session["student_model"]
        questions_asked = session["questions_asked"]
        
        # Store answer
        session["answers_given"].append(user_answer)
        session["turn_number"] += 1
        
        # For first 3 turns, use fixed openers
        if turn < 3:
            next_question = self._get_next_opener(session)
            
            # Update current question in list
            current_q = self.opener_questions[turn]["text"]
            if current_q not in questions_asked:
                questions_asked.append(current_q)
            
            return {
                "question": next_question,
                "branch_scores": student_model.calculate_branch_scores(),
                "confidence": student_model.hypothesis_confidence,
                "is_complete": False,
                "top_branches": student_model.get_top_branches(3),
                "trait_breakdown": self._get_trait_breakdown(student_model),
                "student_model": student_model
            }
        
        # Check stop condition BEFORE generating next question
        if self._should_stop(student_model, turn + 1, questions_asked):
            session["is_complete"] = True
            return self._build_completion_result(session)
        
        # After openers, use LLM for contextual questions
        if llm_client and session.get("llm_enabled", True):
            try:
                result = self._process_with_llm(
                    session,
                    user_answer,
                    llm_client
                )
                return result
            except Exception as e:
                logger.error(f"❌ LLM processing failed: {e}")
                # Don't stop on LLM failure - try fallback question
                weakest_trait = self._get_most_uncertain_trait(student_model)
                fallback_q = self._get_fallback_question(weakest_trait)
                questions_asked.append(fallback_q)
                
                return {
                    "question": {"text": fallback_q, "type": "open"},
                    "branch_scores": student_model.calculate_branch_scores(),
                    "confidence": student_model.hypothesis_confidence,
                    "is_complete": False,
                    "top_branches": student_model.get_top_branches(3),
                    "trait_breakdown": self._get_trait_breakdown(student_model),
                    "student_model": student_model
                }
        
        # Fallback when no LLM available
        weakest_trait = self._get_most_uncertain_trait(student_model)
        fallback_q = self._get_fallback_question(weakest_trait)
        questions_asked.append(fallback_q)
        
        return {
            "question": {"text": fallback_q, "type": "open"},
            "branch_scores": student_model.calculate_branch_scores(),
            "confidence": student_model.hypothesis_confidence,
            "is_complete": False,
            "top_branches": student_model.get_top_branches(3),
            "trait_breakdown": self._get_trait_breakdown(student_model),
            "student_model": student_model
        }
    
    def _get_next_opener(self, session: dict[str, Any]) -> dict[str, Any]:
        """Get next fixed opener question."""
        turn = session["turn_number"]
        if turn < len(self.opener_questions):
            q = self.opener_questions[turn]
            return {
                "text": q["text"],
                "id": q.get("id", f"opener_{turn}"),
                "type": "open",
                "stage": "personality"
            }
        return {"text": "Tell me more about your interests.", "type": "open"}
    
    def _process_with_llm(
        self,
        session: dict[str, Any],
        user_answer: str,
        llm_client
    ) -> dict[str, Any]:
        """Process answer using LLM to extract insights and generate next question."""
        student_model: StudentModel = session["student_model"]
        questions_asked = session["questions_asked"]
        turn = session["turn_number"]
        
        # Get the question that was just answered
        last_question = questions_asked[-1] if questions_asked else "initial question"
        
        # Identify which trait needs the most attention
        weakest_trait = self._get_most_uncertain_trait(student_model)
        
        # Build extraction prompt with target trait
        prompt = build_extraction_prompt(
            student_answer=user_answer,
            question_asked=last_question,
            student_model=student_model.to_dict(),
            questions_asked_so_far=questions_asked,
            current_stage=session["current_stage"],
            turn_number=turn,
            target_trait=weakest_trait  # NEW: tell LLM which trait to probe
        )
        
        # Call LLM
        try:
            response_text = llm_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1200  # Increased from 800 to prevent truncation
            )
            
            # Parse JSON response
            llm_output = self._parse_llm_json(response_text)
            
            if not llm_output:
                logger.error(f"❌ Failed to parse LLM response, using fallback")
                # Return minimal valid structure to prevent crash
                weakest = self._get_most_uncertain_trait(student_model)
                fallback_question = self._get_fallback_question(weakest)
                
                # Still add to questions asked
                questions_asked.append(fallback_question)
                
                return {
                    "question": {"text": fallback_question, "type": "open", "reasoning": "LLM parsing failed, using fallback"},
                    "branch_scores": student_model.calculate_branch_scores(),
                    "confidence": student_model.hypothesis_confidence,
                    "is_complete": False,
                    "top_branches": student_model.get_top_branches(3),
                    "trait_breakdown": self._get_trait_breakdown(student_model),
                    "student_model": student_model,
                    "target_trait": weakest
                }
            
            # Apply updates to student model
            trait_updates = llm_output.get("trait_updates", {})
            profile_updates = llm_output.get("profile_updates", {})
            student_model.apply_updates(trait_updates, profile_updates)
            
            # Update hypothesis
            student_model.branch_hypothesis = llm_output.get("branch_hypothesis", "unknown")
            student_model.hypothesis_confidence = llm_output.get("hypothesis_confidence", 0.0)
            
            # Get next question
            next_question_text = llm_output.get("next_question", "")
            next_question_reasoning = llm_output.get("next_question_reasoning", "")
            
            # Check for duplicate question
            if self._is_duplicate_question(next_question_text, questions_asked):
                logger.warning(f"⚠️ Duplicate question detected, retrying...")
                
                # Build retry prompt with target trait
                retry_prompt = build_retry_prompt(
                    failed_question=next_question_text,
                    reason="Too similar to a previously asked question",
                    questions_asked_so_far=questions_asked,
                    student_model=student_model.to_dict(),
                    current_stage=session["current_stage"]
                )
                retry_prompt += f"\n\nREMINDER: Your next question must target: {weakest_trait}"
                
                response_text = llm_client.generate(
                    prompt=retry_prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.8,
                    max_tokens=300
                )
                retry_output = self._parse_llm_json(response_text)
                if retry_output and "next_question" in retry_output:
                    next_question_text = retry_output["next_question"]
            
            # Add to questions asked
            if next_question_text:
                questions_asked.append(next_question_text)
            
            # Check stop condition
            is_complete = self._should_stop(student_model, turn + 1, questions_asked)
            session["is_complete"] = is_complete
            
            # Build result
            return {
                "question": {"text": next_question_text, "type": "open", "reasoning": next_question_reasoning},
                "branch_scores": student_model.calculate_branch_scores(),
                "confidence": student_model.hypothesis_confidence,
                "is_complete": is_complete,
                "top_branches": student_model.get_top_branches(3),
                "trait_breakdown": self._get_trait_breakdown(student_model),
                "student_model": student_model,
                "llm_reasoning": next_question_reasoning,
                "target_trait": weakest_trait  # For debugging
            }
            
        except Exception as e:
            logger.error(f"❌ LLM processing error: {e}")
            raise
    
    def _parse_llm_json(self, response_text: str) -> Optional[dict]:
        """Parse JSON from LLM response, handling markdown fences and truncation."""
        try:
            # Remove markdown code fences if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # Check for truncation markers (ellipsis)
            if "..." in text or "…" in text:
                logger.warning(f"⚠️ LLM response appears truncated (contains ellipsis)")
                # Try to extract what we can
                text = text.replace("...", "").replace("…", "")
            
            # Try to parse JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Try to fix common issues
                # Remove trailing commas
                text = text.replace(",\n}", "\n}").replace(",\n]", "\n]")
                # Remove comments (// or #)
                lines = text.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove inline comments
                    if '//' in line:
                        line = line.split('//')[0]
                    if '#' in line:
                        line = line.split('#')[0]
                    cleaned_lines.append(line)
                text = '\n'.join(cleaned_lines)
                
                return json.loads(text)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            logger.error(f"Response (first 500 chars): {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected parsing error: {e}")
            return None
    
    def _is_duplicate_question(self, question: str, asked: list[str]) -> bool:
        """Check if question is too similar to already asked questions."""
        if not question or not asked:
            return False
        
        question_lower = question.lower()
        for q in asked:
            if self._similarity(question_lower, q.lower()) > 0.7:
                return True
        return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity between two texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0
    
    def _retry_question_generation(
        self,
        session: dict[str, Any],
        failed_question: str,
        llm_client
    ) -> str:
        """Retry question generation when duplicate detected."""
        retry_prompt = build_retry_prompt(
            failed_question=failed_question,
            reason="Too similar to a previously asked question",
            questions_asked_so_far=session["questions_asked"],
            student_model=session["student_model"].to_dict(),
            current_stage=session["current_stage"]
        )
        
        try:
            response = llm_client.generate(
                prompt=retry_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.8,
                max_tokens=300
            )
            
            retry_output = self._parse_llm_json(response)
            if retry_output and "next_question" in retry_output:
                return retry_output["next_question"]
        except Exception as e:
            logger.error(f"❌ Retry failed: {e}")
        
        # Ultimate fallback
        return "What else would you like to share about yourself?"
    
    def _advance_stage(self, current_stage: str) -> str:
        """Advance to next counseling stage."""
        stage_order = ["personality", "interest_probes", "thinking_style", "aversion_check", "confirmation"]
        try:
            idx = stage_order.index(current_stage)
            return stage_order[idx + 1] if idx < len(stage_order) - 1 else "confirmation"
        except ValueError:
            return "interest_probes"
    
    def _should_stop(self, student_model: StudentModel, turn: int, questions_asked: list) -> bool:
        """
        Stop only when ALL conditions are met.
        Never stop early just because count is reached without full coverage.
        
        Conditions:
        1. At least 8 total questions asked (3 openers + 5 LLM minimum)
        2. All 7 numeric traits have at least one real observation (not default 0.5)
        3. All 3 categorical traits have been observed (not None)
        4. hypothesis_confidence >= 0.85
        5. Hard cap: never exceed 15 questions
        """
        # Hard cap - never exceed 15 questions
        if turn >= 15:
            logger.info(f"[STOP] Hard cap reached at turn {turn}")
            return True
        
        # Minimum 8 questions always
        if turn < 8:
            logger.debug(f"[CONTINUE] Only {turn} questions, need at least 8")
            return False
        
        # Check numeric trait coverage - all must have moved from default 0.5
        numeric_traits = {
            "math_aptitude": student_model.math_aptitude,
            "logical_thinking": student_model.logical_thinking,
            "creativity": student_model.creativity,
            "hands_on": student_model.hands_on,
            "spatial_reasoning": student_model.spatial_reasoning,
            "biology_interest": student_model.biology_interest,
            "problem_solving": student_model.problem_solving,
        }
        
        uncovered_numeric = []
        for trait, value in numeric_traits.items():
            # Check if still at default (within small epsilon)
            if abs(value - 0.5) < 0.01:
                uncovered_numeric.append(trait)
        
        if uncovered_numeric:
            logger.debug(f"[CONTINUE] Uncovered numeric traits: {uncovered_numeric}")
            return False
        
        # Check categorical trait coverage - all must have been observed
        categorical_traits = {
            "risk_appetite": student_model.risk_appetite,
            "work_style": student_model.work_style,
            "memory_preference": student_model.memory_preference,
        }
        
        uncovered_categorical = []
        for trait, value in categorical_traits.items():
            if value is None:
                uncovered_categorical.append(trait)
        
        if uncovered_categorical:
            logger.debug(f"[CONTINUE] Uncovered categorical traits: {uncovered_categorical}")
            return False
        
        # Check confidence threshold
        if student_model.hypothesis_confidence < 0.85:
            logger.debug(f"[CONTINUE] Confidence {student_model.hypothesis_confidence:.2f} < 0.85")
            return False
        
        # All conditions met
        logger.info(f"[STOP] All conditions met at turn {turn}: "
                   f"all traits covered, confidence {student_model.hypothesis_confidence:.2f}")
        return True
    
    def _get_most_uncertain_trait(self, student_model: StudentModel) -> str:
        """
        Returns the trait name that needs the most attention.
        
        Priority:
        1. Categorical traits still None (never observed)
        2. Numeric traits still at default 0.5
        3. Numeric traits closest to 0.5 (most uncertain)
        """
        numeric_traits = {
            "math_aptitude": student_model.math_aptitude,
            "logical_thinking": student_model.logical_thinking,
            "creativity": student_model.creativity,
            "hands_on": student_model.hands_on,
            "spatial_reasoning": student_model.spatial_reasoning,
            "biology_interest": student_model.biology_interest,
            "problem_solving": student_model.problem_solving,
        }
        
        categorical_traits = {
            "risk_appetite": student_model.risk_appetite,
            "work_style": student_model.work_style,
            "memory_preference": student_model.memory_preference,
        }
        
        # First priority: categorical traits never observed
        for trait, value in categorical_traits.items():
            if value is None:
                logger.debug(f"[TARGET] Categorical trait never observed: {trait}")
                return trait
        
        # Second priority: numeric traits still at default
        for trait, value in numeric_traits.items():
            if abs(value - 0.5) < 0.01:
                logger.debug(f"[TARGET] Numeric trait at default: {trait}")
                return trait
        
        # Third priority: trait closest to 0.5 (most uncertain)
        most_uncertain = min(numeric_traits.items(), key=lambda t: abs(t[1] - 0.5))
        logger.debug(f"[TARGET] Most uncertain trait: {most_uncertain[0]} = {most_uncertain[1]:.2f}")
        return most_uncertain[0]
    
    def _get_fallback_question(self, trait: str) -> str:
        """
        Hardcoded fallback questions per trait — used only if LLM fails.
        These are Class-12 friendly — no technical jargon.
        """
        FALLBACKS = {
            "math_aptitude": "When you solve a maths problem and get it right, does it feel satisfying or just relieving?",
            "logical_thinking": "If a rule or a system doesn't make sense to you, do you question it or just follow it?",
            "creativity": "Have you ever made something — a drawing, a story, a plan, anything — just because you wanted to?",
            "hands_on": "When something at home stops working, what is your first instinct — fix it yourself or call someone?",
            "spatial_reasoning": "Can you picture how a piece of furniture would look in a room before it arrives, or do you need to see it?",
            "biology_interest": "Do living things — plants, animals, the human body — ever genuinely fascinate you?",
            "problem_solving": "When you're stuck on something for a long time, do you find that feeling annoying or interesting?",
            "risk_appetite": "Would you rather have a fixed salary at a stable company or take a chance on something uncertain but exciting?",
            "work_style": "In any group situation — class project, sports, anything — do you prefer leading, following, or working alone?",
            "memory_preference": "In school, did you prefer subjects where you understood concepts deeply, or ones where you could just memorise and reproduce?",
        }
        
        question = FALLBACKS.get(trait, "Tell me more about what kind of work you imagine yourself doing every day.")
        logger.info(f"[FALLBACK] Using fallback question for trait: {trait}")
        return question
    
    def get_uncovered_traits(self, student_model: StudentModel) -> dict:
        """
        Get lists of traits that haven't been adequately measured yet.
        Used for debugging and monitoring.
        """
        numeric_traits = {
            "math_aptitude": student_model.math_aptitude,
            "logical_thinking": student_model.logical_thinking,
            "creativity": student_model.creativity,
            "hands_on": student_model.hands_on,
            "spatial_reasoning": student_model.spatial_reasoning,
            "biology_interest": student_model.biology_interest,
            "problem_solving": student_model.problem_solving,
        }
        
        categorical_traits = {
            "risk_appetite": student_model.risk_appetite,
            "work_style": student_model.work_style,
            "memory_preference": student_model.memory_preference,
        }
        
        uncovered_numeric = [t for t, v in numeric_traits.items() if abs(v - 0.5) < 0.01]
        uncovered_categorical = [t for t, v in categorical_traits.items() if v is None]
        
        return {
            "numeric": uncovered_numeric,
            "categorical": uncovered_categorical,
            "total_uncovered": len(uncovered_numeric) + len(uncovered_categorical)
        }
    
    def _get_trait_breakdown(self, model: StudentModel) -> dict[str, float]:
        """Get trait scores as dict for frontend display."""
        return {
            "math_aptitude": model.math_aptitude,
            "logical_thinking": model.logical_thinking,
            "creativity": model.creativity,
            "hands_on": model.hands_on,
            "spatial_reasoning": model.spatial_reasoning,
            "biology_interest": model.biology_interest,
            "problem_solving": model.problem_solving
        }
    
    def _build_completion_result(self, session: dict[str, Any]) -> dict[str, Any]:
        """Build result when session is complete."""
        student_model: StudentModel = session["student_model"]
        branch_scores = student_model.calculate_branch_scores()
        top_branch = max(branch_scores.items(), key=lambda x: x[1])
        
        return {
            "question": None,
            "branch_scores": branch_scores,
            "confidence": student_model.hypothesis_confidence,
            "is_complete": True,
            "top_branches": student_model.get_top_branches(3),
            "trait_breakdown": self._get_trait_breakdown(student_model),
            "student_model": student_model,
            "recommended_branch": top_branch[0]
        }
    
    def _build_fallback_result(self, session: dict[str, Any]) -> dict[str, Any]:
        """Build fallback result when LLM unavailable."""
        student_model: StudentModel = session["student_model"]
        
        return {
            "question": {"text": "What else would you like me to know about you?", "type": "open"},
            "branch_scores": student_model.calculate_branch_scores(),
            "confidence": student_model.hypothesis_confidence,
            "is_complete": False,
            "top_branches": student_model.get_top_branches(3),
            "trait_breakdown": self._get_trait_breakdown(student_model),
            "student_model": student_model
        }
    
    def build_report(self, session: dict[str, Any]) -> dict[str, Any]:
        """Build final counseling report."""
        student_model: StudentModel = session["student_model"]
        branch_scores = student_model.calculate_branch_scores()
        top_branches = student_model.get_top_branches(3)
        
        recommended_branch = top_branches[0]["branch"] if top_branches else "CS"
        
        # Build branch summary
        branch_description = get_branch_description(recommended_branch)
        
        summary_parts = []
        if student_model.interests:
            summary_parts.append(f"Based on your interests in {', '.join(student_model.interests[:3])}")
        if student_model.hands_on > 0.7:
            summary_parts.append("your hands-on approach")
        if student_model.logical_thinking > 0.7:
            summary_parts.append("your logical thinking")
        
        branch_summary = (
            f"{branch_description}. " +
            (" and ".join(summary_parts) if summary_parts else "Based on your responses") +
            ", this seems like a great fit for you."
        )
        
        return {
            "recommended_branch": recommended_branch,
            "branch_summary": branch_summary,
            "branch_scores": branch_scores,
            "confidence": student_model.hypothesis_confidence,
            "top_branches": top_branches,
            "trait_breakdown": self._get_trait_breakdown(student_model),
            "student_interests": student_model.interests,
            "student_motivations": student_model.motivations,
            "student_aversions": student_model.aversions
        }
