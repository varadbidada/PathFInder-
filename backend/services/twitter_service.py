"""
services/twitter_service.py — High-Level Twitter Analysis Orchestrator

Combines scraping + analysis + LLM summarisation into a single async call.
Integrates with the existing Groq-based ai_service for final narrative generation.
Results are cached in-memory (TTL: 24h) to avoid redundant API calls.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from services.twitter_scraper import fetch_college_tweets, Tweet
from services.twitter_analyzer import (
    analyse_college_tweets,
    TwitterAnalysisReport,
    CategoryInsight,
)
from config import settings

logger = logging.getLogger(__name__)

# ── Simple in-memory cache (keyed by college name) ───────────────────────────
_cache: dict[str, tuple[float, TwitterAnalysisReport]] = {}
CACHE_TTL = 86_400  # 24 hours


def _get_cached(college_name: str) -> Optional[TwitterAnalysisReport]:
    entry = _cache.get(college_name)
    if entry and (time.time() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _set_cache(college_name: str, report: TwitterAnalysisReport) -> None:
    _cache[college_name] = (time.time(), report)


# ── LLM narrative generation ──────────────────────────────────────────────────

async def _generate_llm_narrative(
    college_name: str,
    report: TwitterAnalysisReport,
) -> str:
    """
    Use Groq to generate a concise, realistic narrative from the analysis report.
    The LLM is given aggregated statistics — NOT raw tweets — to prevent
    hallucination from 1-2 anecdotal tweets.
    """
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.groq_api_key)
    except Exception:
        return report.realistic_summary

    # Build a structured stats block for the LLM
    cat_lines = []
    for cat, insight in report.category_insights.items():
        if insight.tweet_count >= 5:
            cat_lines.append(
                f"  - {cat.replace('_', ' ').title()}: "
                f"{insight.tweet_count} tweets, "
                f"sentiment={insight.sentiment_label} ({insight.sentiment_score:+.2f}), "
                f"confidence={insight.confidence:.0%}"
            )

    stats_block = f"""
College: {college_name}
Sample size: {report.sample_size} tweets
Overall sentiment: {report.overall_sentiment_label} (score: {report.overall_sentiment_score:+.3f})
Positive: {report.positive_ratio:.0%} | Negative: {report.negative_ratio:.0%} | Neutral: {report.neutral_ratio:.0%}
Confidence: {report.overall_confidence:.0%}
Top emotions: {', '.join(report.top_emotions)}
Toxicity rate: {report.toxicity_rate:.1%}
Verified tweet ratio: {report.verified_tweet_ratio:.1%}

Category breakdown:
{chr(10).join(cat_lines) if cat_lines else '  No category with ≥5 tweets.'}

Dominant opinion (from largest tweet cluster):
  "{report.dominant_opinion[:200]}"

Minority opinion (from smallest valid cluster):
  "{report.minority_opinion[:200]}"

Data quality: {report.data_quality_note}
""".strip()

    prompt = f"""You are an objective college analyst. Based ONLY on the following aggregated 
Twitter/X sentiment statistics (NOT individual tweets), write a realistic 4-6 sentence 
summary of student sentiment about {college_name}.

Rules:
- Do NOT invent facts not present in the statistics.
- Acknowledge uncertainty when confidence is low.
- Mention the sample size and confidence level.
- Highlight both dominant and minority opinions.
- Be balanced — mention both positives and negatives.
- Do NOT use superlatives or marketing language.

Statistics:
{stats_block}

Write the summary now:"""

    try:
        response = await client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=400,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM narrative generation failed: {e}")
        return report.realistic_summary


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _serialise_category(insight: CategoryInsight) -> dict:
    return {
        "category": insight.category,
        "tweet_count": insight.tweet_count,
        "sentiment_score": insight.sentiment_score,
        "sentiment_label": insight.sentiment_label,
        "positive_ratio": insight.positive_ratio,
        "negative_ratio": insight.negative_ratio,
        "neutral_ratio": insight.neutral_ratio,
        "dominant_emotions": insight.dominant_emotions,
        "representative_tweets": insight.representative_tweets,
        "cluster_count": insight.cluster_count,
        "confidence": insight.confidence,
    }


def serialise_report(report: TwitterAnalysisReport, narrative: str) -> dict:
    """Convert a TwitterAnalysisReport to a JSON-serialisable dict."""
    return {
        "college_name": report.college_name,
        "sample_size": report.sample_size,
        "overall": {
            "sentiment_score": report.overall_sentiment_score,
            "sentiment_label": report.overall_sentiment_label,
            "positive_ratio": report.positive_ratio,
            "negative_ratio": report.negative_ratio,
            "neutral_ratio": report.neutral_ratio,
            "confidence": report.overall_confidence,
            "top_emotions": report.top_emotions,
            "toxicity_rate": report.toxicity_rate,
            "verified_tweet_ratio": report.verified_tweet_ratio,
        },
        "opinions": {
            "dominant": report.dominant_opinion,
            "minority": report.minority_opinion,
        },
        "categories": {
            cat: _serialise_category(insight)
            for cat, insight in report.category_insights.items()
        },
        "summary": narrative,
        "realistic_summary": report.realistic_summary,
        "data_quality_note": report.data_quality_note,
    }


# ── Main public API ───────────────────────────────────────────────────────────

async def get_twitter_insights(
    college_name: str,
    target_tweet_count: int = 200,
    use_cache: bool = True,
    generate_narrative: bool = True,
) -> dict:
    """
    Full pipeline: scrape → analyse → LLM narrative → serialised report.

    Args:
        college_name: Canonical college name (e.g. "IIT Bombay")
        target_tweet_count: Minimum tweets to scrape (default 200)
        use_cache: Return cached result if available (default True)
        generate_narrative: Use Groq to generate a narrative summary (default True)

    Returns:
        JSON-serialisable dict with full analysis report.
    """
    # Cache check
    if use_cache:
        cached = _get_cached(college_name)
        if cached:
            logger.info(f"[Twitter] Cache hit for '{college_name}'")
            narrative = await _generate_llm_narrative(college_name, cached) if generate_narrative else cached.realistic_summary
            return serialise_report(cached, narrative)

    # Scrape
    logger.info(f"[Twitter] Starting scrape for '{college_name}' (target: {target_tweet_count})")
    tweets: list[Tweet] = await fetch_college_tweets(college_name, target_count=target_tweet_count)

    # Analyse
    report = analyse_college_tweets(college_name, tweets)

    # Cache
    _set_cache(college_name, report)

    # LLM narrative
    narrative = (
        await _generate_llm_narrative(college_name, report)
        if generate_narrative
        else report.realistic_summary
    )

    return serialise_report(report, narrative)


async def get_twitter_insights_batch(
    college_names: list[str],
    target_tweet_count: int = 200,
) -> dict[str, dict]:
    """
    Analyse multiple colleges concurrently (with a concurrency cap of 3).
    """
    semaphore = asyncio.Semaphore(3)

    async def _bounded(name: str) -> tuple[str, dict]:
        async with semaphore:
            result = await get_twitter_insights(name, target_tweet_count)
            return name, result

    tasks = [_bounded(name) for name in college_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: dict[str, dict] = {}
    for item in results:
        if isinstance(item, Exception):
            logger.error(f"Batch Twitter analysis failed: {item}")
        else:
            name, data = item
            output[name] = data
    return output
