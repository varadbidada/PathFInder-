"""
services/reddit_service.py — Enhanced Reddit Insight Scraper
Fetches multi-post, multi-comment Reddit data with quality filtering and sentiment analysis.
"""
from __future__ import annotations
import logging
from typing import Optional
import asyncio
from collections import Counter
from config import settings

logger = logging.getLogger(__name__)

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed. Reddit insights will be unavailable.")


# Sentiment word lists
POSITIVE_WORDS = {"great", "excellent", "amazing", "helpful", "placed", "hired", "good", 
                  "best", "awesome", "fantastic", "love", "wonderful", "outstanding", 
                  "brilliant", "superb", "top", "quality", "recommend"}
NEGATIVE_WORDS = {"bad", "worst", "avoid", "scam", "fake", "corrupt", "ragging", "terrible",
                  "horrible", "poor", "disappointing", "waste", "regret", "pathetic", 
                  "useless", "toxic", "nightmare"}


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


def _calculate_sentiment_score(text: str) -> int:
    """Calculate sentiment score: positive words - negative words."""
    text_lower = text.lower()
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    return positive_count - negative_count


def _build_search_queries(college_name: str) -> list[str]:
    """Generate diverse search queries for a college."""
    return [
        f'"{college_name}" placements review',
        f'"{college_name}" campus life hostel',
        f'"{college_name}" honest review experience'
    ]


async def fetch_college_insights(college_name: str) -> str:
    """
    Search Reddit for posts about college using multiple diverse queries.
    Returns combined text of posts + comments with sentiment analysis.
    
    Features:
    - 3 different search queries for diversity
    - Fetches 5 posts per query (15 total before dedup)
    - Extracts top 5 comments per post (min 80 chars)
    - Filters posts with score < 5 (unless < 3 posts total)
    - Deduplicates by submission URL
    - Calculates sentiment score
    - Warns if all posts from single subreddit
    - Returns up to 5000 chars
    """
    if not PRAW_AVAILABLE:
        return ""

    clean_name = college_name.replace(" (Other Region)", "").strip()
    queries = _build_search_queries(clean_name)

    def _fetch_sync() -> str:
        reddit = _get_reddit_client()
        if reddit:
            try:
                return _fetch_with_praw(reddit, queries, clean_name)
            except Exception as e:
                logger.warning(f"PRAW fetch failed for {college_name}: {e}. Falling back to public JSON.")

        # Fallback to public JSON API
        try:
            return _fetch_with_json(queries, clean_name)
        except Exception as e:
            logger.error(f"Fallback Reddit JSON fetch failed for {college_name}: {e}")
            return ""

    # Run synchronous fetch in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync)


def _fetch_with_praw(reddit, queries: list[str], college_name: str) -> str:
    """Fetch Reddit data using PRAW with full comment support."""
    seen_urls = set()
    all_posts = []
    subreddit_counts = Counter()
    
    # Fetch posts from all queries
    for query in queries:
        try:
            for submission in reddit.subreddit("all").search(query, limit=8, time_filter="all"):
                url = f"https://reddit.com{submission.permalink}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Extract post data
                post_data = {
                    'title': submission.title,
                    'url': url,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'selftext': submission.selftext[:800] if submission.selftext else "",
                    'subreddit': submission.subreddit.display_name,
                    'comments': []
                }
                
                # Extract top comments
                try:
                    submission.comments.replace_more(limit=2)
                    for comment in submission.comments[:5]:
                        if hasattr(comment, 'body') and len(comment.body) > 80:
                            post_data['comments'].append(comment.body[:400])
                except Exception as e:
                    logger.debug(f"Failed to load comments for {url}: {e}")
                
                all_posts.append(post_data)
                subreddit_counts[post_data['subreddit']] += 1
        except Exception as e:
            logger.debug(f"Query '{query}' failed: {e}")
            continue
    
    return _format_results(all_posts, subreddit_counts, college_name)


def _fetch_with_json(queries: list[str], college_name: str) -> str:
    """Fetch Reddit data using public JSON API with comment fetching."""
    import urllib.request
    import urllib.parse
    import json
    
    seen_urls = set()
    all_posts = []
    subreddit_counts = Counter()
    
    for query in queries:
        try:
            safe_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/search.json?q={safe_query}&sort=relevance&t=all&limit=5"
            
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                permalink = post.get('permalink', '')
                full_url = f"https://reddit.com{permalink}"
                
                if full_url in seen_urls or not permalink:
                    continue
                seen_urls.add(full_url)
                
                post_data = {
                    'title': post.get('title', ''),
                    'url': full_url,
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'selftext': post.get('selftext', '')[:800],
                    'subreddit': post.get('subreddit', 'unknown'),
                    'comments': []
                }
                
                # Fetch comments for this post
                try:
                    comment_url = f"https://www.reddit.com{permalink}.json?limit=10"
                    comment_req = urllib.request.Request(
                        comment_url,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    
                    with urllib.request.urlopen(comment_req, timeout=10) as comment_response:
                        comment_data = json.loads(comment_response.read().decode())
                    
                    # Comments are in response[1]['data']['children']
                    if len(comment_data) > 1:
                        comments_list = comment_data[1].get('data', {}).get('children', [])
                        for comment_child in comments_list[:5]:
                            comment_body = comment_child.get('data', {}).get('body', '')
                            if len(comment_body) > 80:
                                post_data['comments'].append(comment_body[:400])
                except Exception as e:
                    logger.debug(f"Failed to fetch comments for {permalink}: {e}")
                
                all_posts.append(post_data)
                subreddit_counts[post_data['subreddit']] += 1
                
        except Exception as e:
            logger.debug(f"Query '{query}' failed: {e}")
            continue
    
    return _format_results(all_posts, subreddit_counts, college_name)


def _format_results(all_posts: list[dict], subreddit_counts: Counter, college_name: str) -> str:
    """Format posts into a structured string with quality filtering, sentiment analysis, and metadata."""
    if not all_posts:
        return ""
    
    # Filter low-quality posts (score < 5) unless we have very few posts
    if len(all_posts) >= 3:
        all_posts = [p for p in all_posts if p['score'] >= 5]
    
    # If still no posts, return empty
    if not all_posts:
        logger.warning(f"No quality posts found for {college_name} after filtering")
        return ""
    
    # ── Sentiment analysis on each post ───────────────────────────────────────
    try:
        from nlp.sentiment.analyzer import get_sentiment_analyzer
        from nlp.sentiment.cross_verify import get_cross_verification_engine
        
        sentiment_analyzer = get_sentiment_analyzer()
        cross_verifier = get_cross_verification_engine()
        
        # Analyze sentiment for each post
        post_sentiments = []
        for post in all_posts:
            # Combine title, selftext, and comments for sentiment analysis
            combined_text = f"{post['title']} {post['selftext']}"
            if post['comments']:
                combined_text += " " + " ".join(post['comments'])
            
            sentiment = sentiment_analyzer.analyze(combined_text)
            post['sentiment'] = sentiment
            post_sentiments.append(sentiment['compound'])
        
        # Cross-verify sentiments to detect outliers
        verification = cross_verifier.verify(post_sentiments)
        outlier_indices = set(verification['outlier_indices'])
        
        # Remove outlier posts
        if outlier_indices:
            logger.info(f"Removing {len(outlier_indices)} outlier posts for {college_name}")
            all_posts = [p for i, p in enumerate(all_posts) if i not in outlier_indices]
        
        # Log cross-verification results
        logger.info(f"Cross-verification for {college_name}: {verification['consensus_sentiment']} "
                   f"(confidence: {verification['confidence']}, mean: {verification['mean_sentiment']:.2f})")
        
    except Exception as e:
        logger.warning(f"Sentiment analysis failed for {college_name}: {e}")
        # Continue without sentiment analysis
        for post in all_posts:
            post['sentiment'] = {'compound': 0.0, 'method': 'none'}
        verification = None
    
    # Sort by score (engagement) descending
    all_posts.sort(key=lambda p: p['score'], reverse=True)
    
    # Build result string
    results = []
    results.append(f"=== Reddit Insights for {college_name} ===")
    results.append(f"Total posts: {len(all_posts)}")
    
    # Add cross-verification summary if available
    if verification:
        results.append(f"Consensus sentiment: {verification['consensus_sentiment']} (confidence: {verification['confidence']})")
        if verification.get('note'):
            results.append(f"Note: {verification['note']}")
    
    results.append("")
    
    # Check source diversity
    if len(subreddit_counts) == 1:
        single_sub = list(subreddit_counts.keys())[0]
        logger.warning(f"All Reddit posts for {college_name} from single subreddit: r/{single_sub}")
        results.append(f"[WARNING: All sources from single subreddit r/{single_sub} — may be biased]")
        results.append("")
    
    # Add posts with comments and sentiment tags
    combined_text = ""
    for i, post in enumerate(all_posts, 1):
        post_section = []
        
        # Add sentiment tag to post header
        sentiment_tag = f"[Sentiment: {post['sentiment']['compound']:+.2f}]"
        post_section.append(f"--- Post {i} (Score: {post['score']}, Comments: {post['num_comments']}) {sentiment_tag} ---")
        post_section.append(f"Title: {post['title']}")
        post_section.append(f"URL: {post['url']}")
        post_section.append(f"Subreddit: r/{post['subreddit']}")
        
        if post['selftext']:
            post_section.append(f"Post: {post['selftext']}")
        
        if post['comments']:
            post_section.append(f"Top Comments ({len(post['comments'])}):")
            for j, comment in enumerate(post['comments'], 1):
                post_section.append(f"  Comment {j}: {comment}")
        
        post_section.append("")
        
        # Check if adding this post would exceed 5000 chars
        section_text = "\n".join(post_section)
        if len(combined_text) + len(section_text) > 4500:  # Leave room for metadata
            break
        
        combined_text += section_text
        results.append(section_text)
    
    # Calculate overall sentiment score (legacy keyword-based)
    full_text = "\n".join(results)
    sentiment_score = _calculate_sentiment_score(full_text)
    results.append(f"Sentiment score: {sentiment_score:+d} (positive words - negative words)")
    
    final_text = "\n".join(results)
    
    # Cap at 5000 chars
    if len(final_text) > 5000:
        final_text = final_text[:5000] + "\n[Truncated at 5000 chars]"
    
    logger.info(f"Fetched {len(all_posts)} Reddit posts for {college_name} with {sentiment_score:+d} sentiment")
    return final_text
