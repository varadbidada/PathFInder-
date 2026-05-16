"""
services/ai_service.py — Dual-Mode LLM Integration + Reactive Counsellor
Signal extraction and reactive question generation using Ollama (offline) or Groq (online).
Restructured to use reactive counsellor approach instead of fixed question bank.
"""
from __future__ import annotations
import json
import re
import logging
from typing import Optional
from services.llm_client import call_llm
from models.signals import SignalOutput, NEUTRAL_SIGNALS
from config import settings

# ── NLP Pipeline (graceful fallback if not installed) ────────────────────────
try:
    from nlp.intent.classifier import IntentClassifier
    from nlp.entities.extractor import EntityExtractor
    from nlp.embeddings.search import EmbeddingSearch

    _intent_clf = IntentClassifier()
    _entity_ext = EntityExtractor()
    _search     = EmbeddingSearch()

    # Seed knowledge base for semantic search
    _search.index([
        {"id": "1",  "text": "JEE Advanced rank below 1000 qualifies for IIT CS or Electronics."},
        {"id": "2",  "text": "JEE Main rank below 5000 qualifies for NIT CS or Electronics branches."},
        {"id": "3",  "text": "CS Engineering suits students with strong logical thinking and math aptitude."},
        {"id": "4",  "text": "Mechanical Engineering suits students who enjoy hands-on work and spatial problems."},
        {"id": "5",  "text": "Electronics Engineering suits students interested in circuits, signals, and hardware."},
        {"id": "6",  "text": "Civil Engineering suits students with spatial awareness and interest in construction."},
        {"id": "7",  "text": "Budget under 2 lakh per year suits government colleges like NITs and IIITs."},
        {"id": "8",  "text": "Budget above 5 lakh per year opens private colleges like BITS, VIT, Manipal."},
        {"id": "9",  "text": "Students preferring south India should consider NITs in Chennai, Trichy, Surathkal."},
        {"id": "10", "text": "Students preferring north India should consider IIT Delhi, NIT Kurukshetra, DTU."},
        {"id": "11", "text": "BITS Pilani, Hyderabad, and Goa are top private engineering colleges in India."},
        {"id": "12", "text": "IIT Bombay and IIT Delhi are the top ranked IITs for CS and Electronics."},
    ])
    _NLP_AVAILABLE = True
except ImportError:
    _NLP_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Reactive Counsellor System Prompt ────────────────────────────────────────

SYSTEM_PROMPT = """You are Pathfinder, an expert JEE career counsellor with 15 years of experience. You speak naturally like a real human counsellor — warm, curious, and perceptive.

Your goal is to understand what engineering branch suits this student best.

You ask ONE question at a time, reactive to exactly what they just said.
You never repeat a question. You probe interesting signals deeper.
You notice contradictions and gently surface them.
You sound nothing like a form or a chatbot."""


# ── NLP helpers ───────────────────────────────────────────────────────────────

def classify_intent(text: str) -> dict:
    """Classify the intent of a user message."""
    if _NLP_AVAILABLE:
        return _intent_clf.classify(text)
    return {"intent": "general_inquiry", "confidence": 0.5}


def extract_entities(text: str) -> dict:
    """Extract colleges, programs, scores, etc. from user message."""
    if _NLP_AVAILABLE:
        return _entity_ext.extract(text)
    return {}


def search_knowledge(query: str, top_k: int = 3) -> list:
    """Retrieve relevant knowledge snippets for a query."""
    if _NLP_AVAILABLE:
        return _search.query(query, top_k=top_k)
    return []


def enrich_prompt_with_nlp(user_answer: str, question_asked: str) -> str:
    """
    Build extra context from NLP pipeline to inject into LLM prompts.
    Returns a string block to append to prompts.
    """
    if not _NLP_AVAILABLE:
        return ""

    intent    = classify_intent(user_answer)
    entities  = extract_entities(user_answer)
    retrieved = search_knowledge(f"{question_asked} {user_answer}", top_k=2)

    parts = []

    if intent["confidence"] > 0.5:
        parts.append(f"Detected intent: {intent['intent']} ({intent['confidence']:.0%} confidence)")

    entity_parts = []
    for key, vals in entities.items():
        if vals:
            entity_parts.append(f"{key}: {', '.join(str(v) for v in vals)}")
    if entity_parts:
        parts.append("Extracted entities: " + "; ".join(entity_parts))

    if retrieved:
        snippets = "\n".join(f"- {r['text']}" for r in retrieved)
        parts.append(f"Relevant knowledge:\n{snippets}")

    return ("\n\n[NLP Context]\n" + "\n".join(parts)) if parts else ""


# ── Reactive Signal Extraction and Question Generation ──────────────────────

async def extract_signals_and_generate_question(
    user_answer: str,
    question_asked: str,
    conversation_history: list,  # list of {role, content} dicts
    student_profile: dict,       # accumulated profile so far
    questions_asked_so_far: list # list of question strings to avoid repeats
) -> dict:
    """Single LLM call that:
    1. Extracts signals from the student's answer
    2. Updates the student profile
    3. Generates the next natural question
    
    Returns dict with signals + next question.
    """
    asked_summary = "\n".join(f"- {q}" for q in questions_asked_so_far[-5:])
    
    prompt = f"""Student profile so far:
{json.dumps(student_profile, indent=2)}

Last question you asked: {question_asked}

Student just said: "{user_answer}"

Recent questions already asked (DO NOT repeat these):
{asked_summary}

Your task — return ONLY this JSON structure:
{{
  "signal_updates": {{
    "Math_Aptitude": <0.0-1.0 or null if not mentioned>,
    "Logical_Thinking": <0.0-1.0 or null>,
    "Creativity": <0.0-1.0 or null>,
    "Manual_Work": <0.0-1.0 or null>,
    "Spatial_Reasoning": <0.0-1.0 or null>,
    "Biology_Interest": <0.0-1.0 or null>,
    "Problem_Solving": <0.0-1.0 or null>,
    "Risk_Level": <"low"/"medium"/"high" or null>,
    "Introvert_Extrovert": <"introvert"/"extrovert"/"ambivert" or null>
  }},
  "profile_updates": {{
    "confirmed_strengths": [<list of strings, add new ones>],
    "confirmed_weaknesses": [<list of strings>],
    "expressed_interests": [<list of strings>],
    "contradictions": [<list if student contradicted something earlier>]
  }},
  "branch_hypothesis": "<your current best guess: CS/ECE/Mech/Civil/Chemical/other>",
  "confidence": <0.0-1.0 how confident you are in branch hypothesis>,
  "next_question": "<your natural follow-up question — reactive to what they just said>",
  "reasoning": "<1 sentence: why you chose this specific next question>"
}}

Rules:
- Only set signal values you actually observed in this answer. Use null for others.
- next_question must be ONE question only, no lists, no "or" questions
- next_question must not be semantically similar to any question in the recent list
- next_question should probe the most valuable unknown given current profile
- Sound like a real human counsellor, not a form"""

    result = call_llm(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        expect_json=True,
        temperature=0.75,
        max_tokens=700
    )
    
    # Apply defaults if LLM returned empty
    if not result:
        result = {
            "signal_updates": {},
            "profile_updates": {},
            "branch_hypothesis": "unknown",
            "confidence": 0.0,
            "next_question": "Tell me about a subject or activity you genuinely enjoy outside of studies.",
            "reasoning": "fallback question"
        }
    
    return result


async def get_reactive_question(session_state: dict) -> str:
    """Disabled reactive question generation - return None to force fallback"""
    logger.info("Reactive question generation disabled - using fallback")
    return None  # Force fallback to question bank


# ── Legacy Signal Extraction (Backward Compatible) ───────────────────────────

SIGNAL_EXTRACTION_SYSTEM = """You are a psychometric signal extractor for an AI career counsellor.
Analyze the student's conversational answer and extract the following signals strictly as a JSON object.
Do not include any explanation — ONLY output valid JSON.

CRITICAL: Each dimension has TWO values:
- _ability: How skilled/capable the student is at this (0.0-1.0)
- _enthusiasm: How much they ENJOY/are PASSIONATE about this (0.0-1.0)

These are INDEPENDENT. A student can be good at something but hate it (high ability, low enthusiasm).
Or they can love something but be a beginner (low ability, high enthusiasm).

JSON Schema to return:
{
  "Logical_Thinking_ability": <float 0.0-1.0>,
  "Logical_Thinking_enthusiasm": <float 0.0-1.0>,
  "Creativity_ability": <float 0.0-1.0>,
  "Creativity_enthusiasm": <float 0.0-1.0>,
  "Manual_Work_ability": <float 0.0-1.0>,
  "Manual_Work_enthusiasm": <float 0.0-1.0>,
  "Spatial_Awareness_ability": <float 0.0-1.0>,
  "Spatial_Awareness_enthusiasm": <float 0.0-1.0>,
  "Biology_Interest_ability": <float 0.0-1.0>,
  "Biology_Interest_enthusiasm": <float 0.0-1.0>,
  "Problem_Solving_ability": <float 0.0-1.0>,
  "Problem_Solving_enthusiasm": <float 0.0-1.0>,
  "Communication_ability": <float 0.0-1.0>,
  "Communication_enthusiasm": <float 0.0-1.0>,
  "Math_Aptitude_ability": <float 0.0-1.0>,
  "Math_Aptitude_enthusiasm": <float 0.0-1.0>,
  "Introvert_Extrovert": "introvert" | "ambivert" | "extrovert",
  "Risk_Level": "low" | "medium" | "high",
  "Exam_Type": "jee_main" | "jee_advanced" | "unknown",
  "Suggested_Fields": ["string"],
  "Confidence": <float 0.0-1.0>
}

Rules:
- 0.0 = no signal, 1.0 = very strong signal
- Ability = current skill level (can they do it well NOW?)
- Enthusiasm = passion/enjoyment (do they LOVE doing it? would they do it for fun?)
- Exam_Type: Extract from context - "jee_advanced" for IIT aspirants, "jee_main" for NIT/IIIT/state colleges, "unknown" if not mentioned
- Pay attention to negative language: "I'm good at X but I hate it" → high ability, low enthusiasm
- Pay attention to positive language: "I love X, it's my passion" → high enthusiasm (ability may vary)
- Introvert_Extrovert: introvert = prefers solo work/research, extrovert = prefers teamwork/leadership
- Risk_Level: low = risk-averse/safe choices, high = ambitious/willing to take chances
- Confidence = how certain you are about the extraction (not about the student)
- Only output JSON, no markdown, no backticks, no explanation

Examples:
- "I'm great at math but I find it boring" → Math_Aptitude_ability: 0.8, Math_Aptitude_enthusiasm: 0.2
- "I love coding, I do it for fun every day" → Logical_Thinking_enthusiasm: 0.9, Logical_Thinking_ability: 0.7
- "I hate sitting at computers all day" → Logical_Thinking_enthusiasm: 0.1 (even if ability is high)
- "I enjoy working with my hands, building things" → Manual_Work_enthusiasm: 0.8
"""


def _extract_json_from_text(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
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
    """Backward-compatible wrapper — returns SignalOutput object"""
    result = await extract_signals_and_generate_question(
        user_answer=user_answer,
        question_asked=question_asked,
        conversation_history=[],
        student_profile={},
        questions_asked_so_far=[]
    )
    
    # Convert to existing SignalOutput format
    updates = result.get("signal_updates", {})
    
    # Import and return existing SignalOutput model
    return SignalOutput(
        Math_Aptitude_ability=updates.get("Math_Aptitude") or 0.5,
        Math_Aptitude_enthusiasm=updates.get("Math_Aptitude") or 0.5,
        Logical_Thinking_ability=updates.get("Logical_Thinking") or 0.5,
        Logical_Thinking_enthusiasm=updates.get("Logical_Thinking") or 0.5,
        Creativity_ability=updates.get("Creativity") or 0.5,
        Creativity_enthusiasm=updates.get("Creativity") or 0.5,
        Manual_Work_ability=updates.get("Manual_Work") or 0.5,
        Manual_Work_enthusiasm=updates.get("Manual_Work") or 0.5,
        Biology_Interest_ability=updates.get("Biology_Interest") or 0.5,
        Biology_Interest_enthusiasm=updates.get("Biology_Interest") or 0.5,
        Problem_Solving_ability=updates.get("Problem_Solving") or 0.5,
        Problem_Solving_enthusiasm=updates.get("Problem_Solving") or 0.5,
        Risk_Level=updates.get("Risk_Level") or "medium",
        Introvert_Extrovert=updates.get("Introvert_Extrovert") or "ambivert",
    )


# ── Other AI Functions ────────────────────────────────────────────────────────

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
    
    response = call_llm(
        prompt=context,
        system_prompt=system,
        expect_json=False,
        temperature=0.7,
        max_tokens=300
    )
    
    return response if response else question


async def summarize_reddit_insights(college_name: str, raw_text: str) -> list[str]:
    """
    Summarize Reddit posts about a college into 3-4 bullets with confidence levels.
    """
    if not raw_text.strip():
        return []

    prompt = f"""Here are Reddit posts and comments about {college_name}:

{raw_text[:5000]}

Analyze this Reddit data and summarize in exactly 3-4 SHORT, PUNCHY bullet points (maximum 12-15 words per bullet):

1. Overall student sentiment — note if mixed
2. Placement quality and opportunities
3. Campus life and facilities

CRITICAL RULES:
- For each bullet, add a confidence tag: [High], [Medium], or [Low] based on:
  * [High] = 3+ sources agree on the same point
  * [Medium] = 2 sources agree, or general consensus
  * [Low] = Only 1 source, or conflicting information
- If sentiment is mixed (both positive and negative), explicitly say "Mixed sentiment"
- IGNORE any single extreme outlier experience (e.g., one person's horror story if others are positive)
- Focus on patterns and consensus, not individual anecdotes
- If fewer than 3 sources agree on a negative point, do NOT include it. Majority opinion only.

Append a 4th bullet with exactly one primary Source URL from the text.

Return ONLY the 4 bullet points, each on a new line starting with '• '

Example format:
• [High] Strong placements with 90%+ students placed in top companies
• [Medium] Mixed sentiment on hostel facilities — some praise, some complaints
• [Low] Limited data on campus fest culture and extracurriculars
• Source: https://reddit.com/r/..."""

    response = call_llm(
        prompt=prompt,
        expect_json=False,
        temperature=0.3,
        max_tokens=400
    )
    
    if response:
        bullets = [line.strip() for line in response.strip().split('\n') if line.strip().startswith('•')]
        return bullets[:4]
    return []


async def summarize_twitter_insights(college_name: str, tweets: list[dict]) -> list[str]:
    """
    Summarize Twitter/X posts about a college into 3-4 bullets with engagement weighting.
    """
    if not tweets:
        return []

    # Sort tweets by engagement score
    sorted_tweets = sorted(
        tweets,
        key=lambda t: t.get('likes', 0) + 2 * t.get('retweets', 0),
        reverse=True
    )
    
    # Take top 10 by engagement
    top_tweets = sorted_tweets[:10]
    
    # Build engagement-weighted context
    tweet_lines = []
    for i, tweet in enumerate(top_tweets, 1):
        engagement = tweet.get('likes', 0) + 2 * tweet.get('retweets', 0)
        tweet_lines.append(
            f"{i}. [Engagement: {engagement}] {tweet.get('text', '')[:200]}"
        )
    
    tweets_text = "\n".join(tweet_lines)
    
    prompt = f"""Here are the top 10 most-engaged tweets about {college_name} (sorted by likes + 2×retweets):

{tweets_text}

Analyze these tweets and provide exactly 3 bullets (maximum 15 words each):

1. Most common sentiment (positive/negative/mixed) — note if opinions are divided
2. Specific placement companies mentioned (if any) — list actual company names
3. Any red flags raised by multiple users (not just one person)

CRITICAL RULES:
- Weight high-engagement tweets MORE than low-engagement ones
- If multiple tweets disagree, say "Mixed opinions"
- Only mention companies if explicitly named in tweets
- Only flag issues mentioned by 2+ different tweets
- Each bullet must be ≤15 words

Return ONLY the 3 bullet points, each on a new line starting with '• '

Example format:
• Mixed opinions: 80% positive on placements, 20% critical of facilities
• Companies mentioned: Google, Microsoft, Amazon, Goldman Sachs
• Red flag: Multiple users report poor hostel food quality"""

    response = call_llm(
        prompt=prompt,
        expect_json=False,
        temperature=0.3,
        max_tokens=300
    )
    
    if response:
        bullets = [line.strip() for line in response.strip().split('\n') if line.strip().startswith('•')]
        return bullets[:3]
    return []


async def generate_tie_breaker_question(branch_a: str, branch_b: str) -> str:
    """Dynamically generate a tie-breaker question between two branches."""
    prompt = f"""A student is torn between {branch_a} Engineering and {branch_b} Engineering.
Generate ONE specific, engaging question (2 sentences max) that will help differentiate 
their preference. Focus on real-world work scenarios, not theoretical concepts."""

    response = call_llm(
        prompt=prompt,
        expect_json=False,
        temperature=0.8,
        max_tokens=150
    )
    
    return response if response else (
        f"Imagine you're on a project: one team writes the software brain, "
        f"the other team builds the physical hardware. Which team excites you more?"
    )