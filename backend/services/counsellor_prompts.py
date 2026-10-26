"""counsellor_prompts.py — All LLM prompts for Pathfinder counselling.

Single source of truth for every prompt used by the counsellor. main.py and
ai_service.py MUST NOT embed prompt strings inline.
"""
from __future__ import annotations

import json
from typing import Optional


# --------------------------------------------------------------------------
# System prompt — the counsellor's persona
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Pathfinder, a warm and perceptive career counsellor \
helping Indian students choose an engineering branch after Class 12.

The student you are talking to:
- Has JUST finished Class 12 (PCM or PCB)
- Has NEVER studied engineering, coding, or electronics
- Has NO idea what DSA, circuits, APIs, or semesters mean
- Only has reference to: school subjects, hobbies, family background, \
  and vague career ideas picked up from parents, friends, or YouTube

Your job:
- Understand their personality, interests, and thinking style.
- Pick the next single question that reveals the most unknown about them.
- NEVER repeat a question you have already asked.
- NEVER use engineering jargon (no coding, circuits, DSA, software, hardware, \
  algorithms, semesters, branches-as-fields). Translate every idea into \
  Class-12 vocabulary: school subjects, hobbies, daily life, movies, sports, \
  group projects, family situations.
- Keep questions open-ended. Avoid yes/no.
- Be warm. Sound like an older sibling who happens to know a lot about careers.

Output contract: reply ONLY with the JSON object requested. No markdown, \
no commentary, no preamble."""


# --------------------------------------------------------------------------
# Branch hypothesis vocabulary
# --------------------------------------------------------------------------

# What the LLM is allowed to return as a branch_hypothesis.
ALLOWED_BRANCHES = ["CS", "ECE", "Mech", "Civil", "Chemical", "Bio-tech", "unknown"]

# Map from the LLM's vocabulary to the labels used by engines/recommendation.py
# (and the rest of the system). Keep this mapping in one place.
BRANCH_ALIAS_MAP = {
    "CS": "CS",
    "ECE": "Electronics",      # old: Electronics
    "Mech": "Mechanical",
    "Civil": "Civil",
    "Chemical": "Chemical",
    "Bio-tech": "Medical",     # Bio-tech lives under Medical in college data
}


# --------------------------------------------------------------------------
# Trait coverage helpers
# --------------------------------------------------------------------------

NUMERIC_TRAITS = [
    "math_aptitude",
    "logical_thinking",
    "creativity",
    "hands_on",
    "spatial_reasoning",
    "biology_interest",
    "problem_solving",
]

CATEGORICAL_TRAITS = ["risk_appetite", "work_style", "memory_preference"]


def _coverage_notes(student_model: dict, target_trait: Optional[str]) -> str:
    """Build a short paragraph describing which traits still need measuring."""
    notes = []

    numeric_defaults = [
        k for k in NUMERIC_TRAITS
        if abs(float(student_model.get(k, 0.5) or 0.5) - 0.5) < 0.01
    ]
    if numeric_defaults:
        notes.append(
            "Traits NOT yet measured (still at neutral default 0.5): "
            + ", ".join(numeric_defaults)
        )

    categorical_missing = [
        k for k in CATEGORICAL_TRAITS if student_model.get(k) in (None, "")
    ]
    if categorical_missing:
        notes.append(
            "Categorical traits never observed: " + ", ".join(categorical_missing)
        )

    if target_trait:
        notes.append(
            f"MOST IMPORTANT: your next_question MUST help measure "
            f"'{target_trait}'."
        )

    return "\n".join(notes) if notes else "All traits have at least one observation."


# --------------------------------------------------------------------------
# Main extraction + next-question prompt
# --------------------------------------------------------------------------

def build_extraction_prompt(
    student_answer: str,
    question_asked: str,
    student_model: dict,
    questions_asked_so_far: list,
    current_stage: str,
    turn_number: int,
    target_trait: Optional[str] = None,
) -> str:
    """Compose the prompt that asks the LLM to (1) extract trait updates and
    (2) propose the next question targeting the weakest trait."""

    coverage_note = _coverage_notes(student_model, target_trait)

    asked_preview = "\n".join(f"- {q}" for q in (questions_asked_so_far or [])[-8:])
    if not asked_preview:
        asked_preview = "(this is the first turn)"

    model_summary = json.dumps(
        {
            k: v for k, v in (student_model or {}).items()
            if v not in (None, "", [], {})
        },
        indent=2,
        ensure_ascii=False,
    ) or "(empty)"

    target_clause = target_trait or "the biggest gap in trait coverage"

    return f"""Turn {turn_number}. Current stage: {current_stage}.

Trait coverage gaps:
{coverage_note}

Student profile so far:
{model_summary}

You just asked: "{question_asked}"
Student replied: "{student_answer}"

Recent questions already asked — DO NOT repeat or rephrase:
{asked_preview}

Return ONLY this JSON object (no markdown, no commentary):

{{
  "trait_updates": {{
    "math_aptitude":        <0.0-1.0 or null — only if this answer revealed something>,
    "logical_thinking":     <0.0-1.0 or null>,
    "creativity":           <0.0-1.0 or null>,
    "hands_on":             <0.0-1.0 or null>,
    "spatial_reasoning":    <0.0-1.0 or null>,
    "biology_interest":     <0.0-1.0 or null>,
    "problem_solving":      <0.0-1.0 or null>,
    "risk_appetite":        <"low"/"medium"/"high" or null>,
    "work_style":           <"solo"/"team"/"either" or null>,
    "memory_preference":    <"conceptual"/"rote"/"either" or null>
  }},
  "profile_updates": {{
    "interests":        [<short strings, only genuinely new ones>],
    "aversions":        [<short strings>],
    "motivations":      [<short strings>],
    "contradictions":   [<short strings, only if the student said something \
that contradicts an earlier answer>],
    "notable_quotes":   [<short verbatim quotes worth remembering, max 12 words each>]
  }},
  "branch_hypothesis":     "<one of: CS|ECE|Mech|Civil|Chemical|Bio-tech|unknown>",
  "hypothesis_confidence": <0.0-1.0>,
  "next_question":         "<ONE question that helps measure {target_clause}>",
  "next_question_reasoning": "<1 sentence: why this question is the best probe right now>"
}}

Critical rules for next_question:
- Must help measure: {target_clause}
- Must be answerable by a student who has NEVER studied engineering.
- No jargon: no coding, circuits, DSA, algorithms, API, software, hardware.
- Open-ended — never a yes/no question.
- React to what they just said if useful, but still target the gap trait.
- Maximum 25 words. One sentence preferred.
"""


# --------------------------------------------------------------------------
# Confirmation prompt — used once we hit the confirmation stage
# --------------------------------------------------------------------------

def build_confirmation_prompt(
    student_model: dict,
    branch_hypothesis: str,
    turn_number: int,
) -> str:
    interests = student_model.get("interests") or []
    motivations = student_model.get("motivations") or []
    return f"""Turn {turn_number}. We are now in the confirmation stage.

The student has given you enough signal. Their current best-fit branch is:
"{branch_hypothesis}".

Their interests so far: {interests}
Their motivations so far: {motivations}

Write ONE warm confirmation question that:
1. Names the branch you think fits them and why (in plain Class-12 language).
2. Asks whether it feels right or whether something feels off.
3. Does NOT introduce new jargon.
4. Is at most 35 words.

Return ONLY the question string. No JSON, no markdown."""


# --------------------------------------------------------------------------
# Per-trait fallback questions — used when the LLM is unavailable
# --------------------------------------------------------------------------

FALLBACK_QUESTIONS: dict[str, str] = {
    "math_aptitude":
        "Do you enjoy maths more when you have to derive something from scratch, "
        "or when you can apply a known formula quickly?",
    "logical_thinking":
        "When a tough problem appears, do you instinctively break it into smaller "
        "steps before trying to solve it?",
    "creativity":
        "If you had to design something completely new for a school project, "
        "would that feel exciting or draining?",
    "hands_on":
        "When something around you breaks, do you usually try to fix it yourself "
        "or look for someone who can?",
    "spatial_reasoning":
        "When you imagine a building or a room, can you rotate it in your head "
        "and picture it from a different angle?",
    "biology_interest":
        "Would you rather watch a documentary about how the human body works, or "
        "one about how a bridge is built?",
    "problem_solving":
        "When a group project goes off-track, do you usually step in to "
        "reorganise the plan?",
    "risk_appetite":
        "Would you rather pick a safe path you are sure about, or try something "
        "uncertain that excites you more?",
    "work_style":
        "Do you do your best schoolwork alone, or with friends around you?",
    "memory_preference":
        "Do you remember things better when you understand the idea behind them, "
        "or when you revise them many times?",
}


def fallback_question_for(trait: str) -> str:
    return FALLBACK_QUESTIONS.get(
        trait,
        "Tell me more about what kind of work you imagine yourself doing every day.",
    )


# --------------------------------------------------------------------------
# Additional helper functions
# --------------------------------------------------------------------------

def build_fallback_question(current_stage: str, questions_asked_so_far: list[str]) -> str:
    """
    Generate a fallback question if LLM fails.
    
    Args:
        current_stage: Current stage
        questions_asked_so_far: Questions already asked
    
    Returns:
        A safe fallback question
    """
    fallback_questions = {
        "personality": "Tell me about something you're naturally curious about.",
        "interest": "When something around you breaks or doesn't work, what do you do?",
        "thinking": "If something confuses you, do you prefer to figure it out alone or ask someone?",
        "aversion": "Is there any kind of work that would make you really unhappy?",
        "confirmation": "Based on what you've told me, does the path we discussed feel right to you?"
    }
    
    return fallback_questions.get(current_stage, "Tell me more about what interests you.")


def build_retry_prompt(
    failed_question: str,
    reason: str,
    questions_asked_so_far: list[str],
    student_model: dict,
    current_stage: str
) -> str:
    """
    Build prompt for retrying question generation when first attempt failed.
    
    Args:
        failed_question: The question that was rejected
        reason: Why it was rejected
        questions_asked_so_far: All questions asked so far
        student_model: Current student model
        current_stage: Current stage
    
    Returns:
        Retry prompt string
    """
    asked_preview = "\n".join(f"- {q}" for q in questions_asked_so_far[-6:])
    
    return f"""Your previous question was rejected: "{failed_question}"

Reason: {reason}

Questions already asked:
{asked_preview}

Student profile:
{json.dumps(student_model, indent=2)}

Current stage: {current_stage}

Generate a NEW question that:
1. Is completely different from the rejected question
2. Is NOT similar to any question already asked
3. Is relevant to the current stage
4. Probes a valuable unknown about the student
5. Is jargon-free and suitable for a Class 12 student

Return ONLY JSON:
{{
  "next_question": "<your new question>",
  "reasoning": "<why this question is different and valuable>"
}}
"""


def get_branch_description(branch: str) -> str:
    """
    Get a simple, Class 12-friendly description of a branch.
    
    Args:
        branch: Branch code (CS, ECE, Mech, Civil, Chemical, Bio-tech)
    
    Returns:
        Simple description string
    """
    descriptions = {
        "CS": "Computer Science is about solving problems with software, building apps, and working with data",
        "ECE": "Electronics & Communication is about understanding how devices work, circuits, and signals",
        "Mech": "Mechanical Engineering is about designing and building physical machines and systems",
        "Civil": "Civil Engineering is about designing structures, buildings, bridges, and infrastructure",
        "Chemical": "Chemical Engineering is about processes, reactions, and transforming materials",
        "Bio-tech": "Biotechnology combines biology with technology to work on health, medicine, and life sciences"
    }
    
    return descriptions.get(branch, "Engineering is about using science and math to solve real-world problems")
