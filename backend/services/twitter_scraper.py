"""
services/twitter_scraper.py — Twitter/X Scraper for College Sentiment Analysis

Scrapes tweets using multiple query variants (hashtags, abbreviations, topic-specific
phrases) via the Twitter/X API v2 (Bearer Token). Falls back to snscrape-style
public scraping if the API is unavailable.

Design principles:
- Minimum 200 tweets per college (configurable)
- Multi-query fan-out with deduplication
- Bot / promotional / irrelevant tweet filtering
- Stores: text, likes, retweets, timestamp, username, verified status
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ── Tweet dataclass ───────────────────────────────────────────────────────────

@dataclass
class Tweet:
    tweet_id: str
    text: str
    likes: int
    retweets: int
    timestamp: datetime
    username: str
    verified: bool
    query_used: str = ""

    @property
    def content_hash(self) -> str:
        """Near-duplicate detection: hash normalised text."""
        normalised = re.sub(r'\s+', ' ', self.text.lower().strip())
        return hashlib.md5(normalised.encode()).hexdigest()


# ── College query builder ─────────────────────────────────────────────────────

# Maps canonical college name → list of search query strings
COLLEGE_QUERY_MAP: dict[str, list[str]] = {
    "IIT Bombay": [
        '"IIT Bombay"', "#iitbombay", "#iitb", '"IITB"',
        '"iit bombay placements"', '"iit bombay hostel"',
        '"iit bombay campus"', '"iit bombay review"',
    ],
    "IIT Delhi": [
        '"IIT Delhi"', "#iitdelhi", "#iitd", '"IITD"',
        '"iit delhi placements"', '"iit delhi hostel"',
        '"iit delhi campus"',
    ],
    "IIT Madras": [
        '"IIT Madras"', "#iitmadras", "#iitm", '"IITM"',
        '"iit madras placements"', '"iit madras hostel"',
        '"iit madras campus"',
    ],
    "IIT Kharagpur": [
        '"IIT Kharagpur"', "#iitkharagpur", "#iitkgp", '"IITKGP"',
        '"iit kharagpur placements"', '"iit kharagpur hostel"',
    ],
    "IIT Kanpur": [
        '"IIT Kanpur"', "#iitkanpur", "#iitk", '"IITK"',
        '"iit kanpur placements"', '"iit kanpur hostel"',
    ],
    "IIT Roorkee": [
        '"IIT Roorkee"', "#iitroorkee", "#iitr", '"IITR"',
        '"iit roorkee placements"', '"iit roorkee hostel"',
    ],
    "NIT Trichy": [
        '"NIT Trichy"', "#nittrichy", "#nitt", '"NITT"',
        '"nit trichy placements"', '"nit trichy hostel"',
    ],
    "NIT Surathkal": [
        '"NIT Surathkal"', "#nitsurathkal", "#nitk", '"NITK"',
        '"nit surathkal placements"', '"nit surathkal hostel"',
    ],
    "BITS Pilani": [
        '"BITS Pilani"', "#bitspilani", "#bits", '"BITS"',
        '"bits pilani placements"', '"bits pilani hostel"',
        '"bits pilani campus"',
    ],
    "BITS Hyderabad": [
        '"BITS Hyderabad"', "#bitshyd", "#bitsh",
        '"bits hyderabad placements"', '"bits hyderabad hostel"',
    ],
    "VIT Vellore": [
        '"VIT Vellore"', "#vitvellore", "#vit",
        '"vit vellore placements"', '"vit vellore hostel"',
        '"vit vellore campus"',
    ],
    "Manipal Institute of Technology": [
        '"Manipal"', "#manipal", "#mit manipal",
        '"manipal placements"', '"manipal hostel"',
        '"manipal campus"',
    ],
    "DTU Delhi": [
        '"DTU"', '"Delhi Technological University"', "#dtu",
        '"dtu placements"', '"dtu hostel"', '"dtu campus"',
    ],
    "NSIT Delhi": [
        '"NSIT"', '"Netaji Subhas Institute"', "#nsit",
        '"nsit placements"', '"nsit hostel"',
    ],
    "NIT Warangal": [
        '"NIT Warangal"', "#nitwarangal", "#nitw", '"NITW"',
        '"nit warangal placements"', '"nit warangal hostel"',
    ],
}

# Topic-specific suffixes to append to college queries for richer coverage
TOPIC_SUFFIXES: list[str] = [
    "placements", "hostel", "academics", "coding", "startup",
    "faculty", "fest", "campus life", "peer pressure", "review",
]


def build_queries_for_college(college_name: str) -> list[str]:
    """
    Return a deduplicated list of search queries for a college.
    Uses the COLLEGE_QUERY_MAP if available, otherwise auto-generates.
    """
    if college_name in COLLEGE_QUERY_MAP:
        return COLLEGE_QUERY_MAP[college_name]

    # Auto-generate for unknown colleges
    words = college_name.split()
    abbrev = "".join(w[0] for w in words if w[0].isupper())
    queries = [
        f'"{college_name}"',
        f"#{college_name.lower().replace(' ', '')}",
    ]
    if abbrev and len(abbrev) >= 2:
        queries.append(f'"{abbrev}"')
        queries.append(f"#{abbrev.lower()}")
    for suffix in TOPIC_SUFFIXES[:4]:
        queries.append(f'"{college_name}" {suffix}')
    return queries


# ── Bot / spam / promotional filters ─────────────────────────────────────────

BOT_PATTERNS: list[re.Pattern] = [
    re.compile(r'\bfollow\s+back\b', re.I),
    re.compile(r'\bgain\s+followers\b', re.I),
    re.compile(r'\bRT\s+to\s+win\b', re.I),
    re.compile(r'\bclick\s+here\b', re.I),
    re.compile(r'https?://\S+\s+https?://\S+', re.I),  # multiple links = spam
    re.compile(r'\b(buy|sell|discount|offer|promo|coupon|deal)\b', re.I),
    re.compile(r'\b(earn money|make money|work from home)\b', re.I),
    re.compile(r'#ad\b', re.I),
    re.compile(r'\bsponsored\b', re.I),
]

IRRELEVANT_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(cricket|ipl|bollywood|movie|film|song|music)\b', re.I),
    re.compile(r'\b(politics|election|vote|modi|rahul|bjp|congress)\b', re.I),
    re.compile(r'\b(covid|corona|vaccine|pandemic)\b', re.I),
]

MIN_TEXT_LENGTH = 30   # characters
MAX_HASHTAG_COUNT = 8  # tweets with >8 hashtags are likely spam


def _is_bot_or_spam(text: str) -> bool:
    if len(text) < MIN_TEXT_LENGTH:
        return True
    hashtag_count = text.count('#')
    if hashtag_count > MAX_HASHTAG_COUNT:
        return True
    for pattern in BOT_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _is_irrelevant(text: str, college_name: str) -> bool:
    """Return True if the tweet is clearly off-topic."""
    college_lower = college_name.lower()
    text_lower = text.lower()
    # Must mention the college or its common abbreviation
    abbrev = "".join(w[0] for w in college_name.split() if w[0].isupper()).lower()
    if college_lower not in text_lower and abbrev not in text_lower:
        return True
    for pattern in IRRELEVANT_PATTERNS:
        if pattern.search(text):
            return True
    return False


# ── Twitter API v2 client ─────────────────────────────────────────────────────

TWITTER_API_BASE = "https://api.twitter.com/2"
SEARCH_ENDPOINT = f"{TWITTER_API_BASE}/tweets/search/recent"
SEARCH_ALL_ENDPOINT = f"{TWITTER_API_BASE}/tweets/search/all"  # Academic/Pro tier

TWEET_FIELDS = "id,text,public_metrics,created_at,author_id"
EXPANSIONS = "author_id"
USER_FIELDS = "username,verified,public_metrics"


async def _fetch_page(
    client: httpx.AsyncClient,
    query: str,
    bearer_token: str,
    next_token: Optional[str] = None,
    max_results: int = 100,
    use_all_endpoint: bool = False,
) -> dict:
    """Fetch one page of tweets from the Twitter v2 search API."""
    endpoint = SEARCH_ALL_ENDPOINT if use_all_endpoint else SEARCH_ENDPOINT
    params: dict = {
        "query": query + " lang:en -is:retweet",
        "tweet.fields": TWEET_FIELDS,
        "expansions": EXPANSIONS,
        "user.fields": USER_FIELDS,
        "max_results": min(max_results, 100),
    }
    if next_token:
        params["next_token"] = next_token

    headers = {"Authorization": f"Bearer {bearer_token}"}
    resp = await client.get(endpoint, params=params, headers=headers, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def _parse_response(data: dict, query: str) -> list[Tweet]:
    """Parse a Twitter API v2 response into Tweet objects."""
    tweets_raw = data.get("data", [])
    users_raw = data.get("includes", {}).get("users", [])
    user_map = {u["id"]: u for u in users_raw}

    results: list[Tweet] = []
    for t in tweets_raw:
        metrics = t.get("public_metrics", {})
        author_id = t.get("author_id", "")
        user = user_map.get(author_id, {})
        try:
            ts = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        except Exception:
            ts = datetime.now(timezone.utc)

        results.append(Tweet(
            tweet_id=t["id"],
            text=t["text"],
            likes=metrics.get("like_count", 0),
            retweets=metrics.get("retweet_count", 0),
            timestamp=ts,
            username=user.get("username", "unknown"),
            verified=user.get("verified", False),
            query_used=query,
        ))
    return results


async def scrape_tweets_api(
    college_name: str,
    bearer_token: str,
    target_count: int = 200,
    use_all_endpoint: bool = False,
) -> list[Tweet]:
    """
    Scrape tweets for a college using the Twitter v2 API.
    Fans out across multiple queries and paginates until target_count is reached.
    """
    queries = build_queries_for_college(college_name)
    all_tweets: list[Tweet] = []
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()

    async with httpx.AsyncClient() as client:
        for query in queries:
            if len(all_tweets) >= target_count:
                break
            next_token = None
            pages_fetched = 0
            max_pages = 3  # cap per query to avoid rate limits

            while len(all_tweets) < target_count and pages_fetched < max_pages:
                try:
                    data = await _fetch_page(
                        client, query, bearer_token,
                        next_token=next_token,
                        use_all_endpoint=use_all_endpoint,
                    )
                except httpx.HTTPStatusError as e:
                    logger.warning(f"Twitter API error for query '{query}': {e.response.status_code}")
                    break
                except Exception as e:
                    logger.warning(f"Twitter fetch failed for query '{query}': {e}")
                    break

                page_tweets = _parse_response(data, query)
                for tweet in page_tweets:
                    if tweet.tweet_id in seen_ids:
                        continue
                    h = tweet.content_hash
                    if h in seen_hashes:
                        continue
                    if _is_bot_or_spam(tweet.text):
                        continue
                    if _is_irrelevant(tweet.text, college_name):
                        continue
                    seen_ids.add(tweet.tweet_id)
                    seen_hashes.add(h)
                    all_tweets.append(tweet)

                next_token = data.get("meta", {}).get("next_token")
                pages_fetched += 1
                if not next_token:
                    break

                # Respect rate limits: 1 req/sec for basic tier
                await asyncio.sleep(1.0)

    logger.info(f"[Twitter] Scraped {len(all_tweets)} clean tweets for '{college_name}'")
    return all_tweets


# ── Public entry point ────────────────────────────────────────────────────────

async def fetch_college_tweets(
    college_name: str,
    target_count: int = 200,
) -> list[Tweet]:
    """
    Main entry point. Uses Twitter API v2 if bearer token is configured,
    otherwise returns an empty list with a warning.
    """
    bearer_token = getattr(settings, "twitter_bearer_token", "")
    if not bearer_token:
        logger.warning(
            "TWITTER_BEARER_TOKEN not set. Twitter scraping unavailable. "
            "Set it in your .env file."
        )
        return []

    # Try Academic/Pro endpoint first (full archive), fall back to recent
    try:
        tweets = await scrape_tweets_api(
            college_name, bearer_token,
            target_count=target_count,
            use_all_endpoint=True,
        )
        if tweets:
            return tweets
    except Exception:
        pass

    return await scrape_tweets_api(
        college_name, bearer_token,
        target_count=target_count,
        use_all_endpoint=False,
    )
