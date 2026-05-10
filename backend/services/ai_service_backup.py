"""
services/ai_service.py — Groq API Integration
Signal extraction from conversation text, with retry and fallback logic.
"""
from __future__ import annotations
import json
import re
import logging
from typing import Optional
from groq import AsyncGroq
from models.signals import SignalOutput, NEUTRAL_SIGNALS
from config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncGroq] = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


SIGNAL_EXTRACTION_SYSTEM = """You are a psychometric signal extractor for an AI career counsellor.
Analyze the student's conversational answer and extract the following signals strictly as a JSON object.
Do not include any explanation — ONLY output valid JSON.

JSON Schema to return:
{
  "Logical_Thinking": <float 0.0-1.0>,
  "Creativity": <float 0.0-1.0>,
  "Manual_Work": <float 0.0-1.0>,
  "Spatial_Awareness": <float 0.0-1.0>,
  "Biology_Interest": <float 0.0-1.0>,
  "Problem_Solving": <float 0.0-1.0>,
  "Communication": <float 0.0-1.0>,
  "Math_Aptitude": <float 0.0-1.0>,
  "Risk_Level": "low" | "medium" | "high",
  "Suggested_Fields": ["string"],
  "Confidence": <float 0.0-1.0>
}

Rules:
- 0.0 = no signal, 1.0 = very strong signal
- Risk_Level: low = risk-averse student, high = ambitious/willing to take chances
- Confidence = how certain you are about the extraction (not about the student)
- Only output JSON, no markdown, no backticks, no explanation
"""


def _extract_json_from_text(text: str) -> dict:
    """Try to extract a JSON object from text, even if surrounded by other content."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from: {text[:200]}")


async def extract_signals(
    user_answer: str,
    question_asked: str,
    conversation_context: str = "",
) -> SignalOutput:
    """
    Extract psychometric signals from a user's answer.
    Retries once on parse failure; falls back to neutral signals.
    """
    prompt = f"""Question asked to student: {question_asked}

Student's answer: {user_answer}

Recent conversation context:
{conversation_context}

Extract signals from this answer as JSON:"""

    for attempt in range(settings.signal_retry_attempts + 1):
        try:
            client = _get_client()
            response = await client.chat.completions.create(
                model=settings.groq_model,
                max_tokens=settings.groq_max_tokens,
                temperature=settings.groq_temperature,
                messages=[
                    {"role": "system", "content": SIGNAL_EXTRACTION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            raw_text = response.choices[0].message.content
            data = _extract_json_from_text(raw_text)
            return SignalOutput(**data)
        except Exception as e:
            logger.warning(f"Signal extraction attempt {attempt + 1} failed: {e}")
            if attempt < settings.signal_retry_attempts:
                continue
            logger.error("All signal extraction attempts failed. Using neutral fallback.")
            return NEUTRAL_SIGNALS


async def generate_counsellor_response(
    question: str,
    conversation_history: str,
    student_signals: Optional[dict] = None,
) -> str:
    """
    Generate a warm, empathetic counsellor reply to follow up on a question.
    """
    system = """You are Pathfinder, a warm and expert AI career counsellor helping Indian 
engineering students choose the right branch and college. Speak naturally, be encouraging, 
and always follow up on what the student said. Keep responses concise (2-4 sentences max).
Never make direct branch or college recommendations — just ask the next question warmly."""

    context = f"""Conversation so far:
{conversation_history}

Next question to transition to: {question}
"""
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=300,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Counsellor response generation failed: {e}")
        return question  # Fall back to showing the raw question


async def summarize_reddit_insights(college_name: str, raw_text: str) -> list[str]:
    """
    Summarize Reddit posts about a college into 3 bullets: sentiment, placement, campus life.
    """
    if not raw_text.strip():
        return []

    prompt = f"""Here are Reddit posts and comments about {college_name}:

{raw_text[:3000]}

Summarize in exactly 3 bullet points:
1. Overall student sentiment
2. Placement quality and opportunities
3. Campus life and facilities

Return ONLY the 3 bullet points, each on a new line starting with '• '"""

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content
        bullets = [line.strip() for line in text.strip().split('\n') if line.strip().startswith('•')]
        return bullets[:3]
    except Exception as e:
        logger.error(f"Reddit summarization failed: {e}")
        return []


async def generate_tie_breaker_question(branch_a: str, branch_b: str) -> str:
    """Dynamically generate a tie-breaker question between two branches."""
    prompt = f"""A student is torn between {branch_a} Engineering and {branch_b} Engineering.
Generate ONE specific, engaging question (2 sentences max) that will help differentiate 
their preference. Focus on real-world work scenarios, not theoretical concepts."""

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=150,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Tie-breaker generation failed: {e}")
        return (
            f"Imagine you're on a project: one team writes the software brain, "
            f"the other team builds the physical hardware. Which team excites you more?"
        )
