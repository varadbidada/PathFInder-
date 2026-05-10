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

    clean_name = college_name.replace(" (Other Region)", "").strip()
    query = f'"{clean_name}" placements'

    def _fetch_sync() -> str:
        reddit = _get_reddit_client()
        if reddit:
            try:
                results = []
                for submission in reddit.subreddit("all").search(query, limit=3, time_filter="all"):
                    results.append(f"Title: {submission.title}")
                    results.append(f"URL: https://reddit.com{submission.permalink}")
                    if submission.selftext:
                        results.append(f"Post: {submission.selftext[:500]}")
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:3]:
                        if len(comment.body) > 50:
                            results.append(f"Comment: {comment.body[:300]}")
                if results:
                    return "\n\n".join(results)
            except Exception as e:
                logger.warning(f"PRAW fetch failed for {college_name} (likely 403 auth error): {e}. Falling back to public JSON.")

        # Fallback to public JSON API if PRAW fails or is unavailable
        try:
            import urllib.request
            import urllib.parse
            import json
            
            safe_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/search.json?q={safe_query}&sort=relevance&t=all&limit=3"
            
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            results = []
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                results.append(f"Title: {post.get('title', '')}")
                results.append(f"URL: https://reddit.com{post.get('permalink', '')}")
                if post.get('selftext'):
                    results.append(f"Post: {post.get('selftext')[:500]}")
            
            return "\n\n".join(results)
        except Exception as e:
            logger.error(f"Fallback Reddit JSON fetch failed for {college_name}: {e}")
            return ""

    # Run synchronous PRAW in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync)
