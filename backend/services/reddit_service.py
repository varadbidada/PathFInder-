"""
services/reddit_service.py — Reddit Insight Scraper
Fetches top posts from Reddit about a college using PRAW.
"""
from __future__ import annotations
import logging
from typing import Optional
import asyncio
from config import settings

logger = logging.getLogger(__name__)

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed. Reddit insights will be unavailable.")


def _get_reddit_client():
    if not PRAW_AVAILABLE:
        return None
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return None
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


async def fetch_college_insights(college_name: str) -> str:
    """
    Search Reddit for posts about college placements/reviews.
    Returns combined text of top posts + comments for AI summarization.
    """
    if not PRAW_AVAILABLE:
        return ""

    query = f'"{college_name}" placements review 2024'

    def _fetch_sync() -> str:
        reddit = _get_reddit_client()
        if not reddit:
            return ""
        try:
            results = []
            for submission in reddit.subreddit("all").search(query, limit=3, time_filter="year"):
                results.append(f"Title: {submission.title}")
                results.append(f"URL: https://reddit.com{submission.permalink}")
                if submission.selftext:
                    results.append(f"Post: {submission.selftext[:500]}")
                submission.comments.replace_more(limit=0)
                for comment in submission.comments[:3]:
                    if len(comment.body) > 50:
                        results.append(f"Comment: {comment.body[:300]}")
            return "\n\n".join(results)
        except Exception as e:
            logger.error(f"Reddit fetch failed for {college_name}: {e}")
            return ""

    # Run synchronous PRAW in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync)
