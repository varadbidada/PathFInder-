# Twitter/X Analysis Pipeline for College Sentiment

## Overview

This module provides a comprehensive Twitter/X analysis pipeline for gathering and analyzing student sentiment about Indian engineering colleges. The system scrapes tweets, performs multi-dimensional NLP analysis, and generates realistic summaries using LLM-based aggregation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Twitter Analysis Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. SCRAPING (twitter_scraper.py)                                │
│     ├─ Twitter API v2 (primary)                                  │
│     ├─ Multi-query fan-out (hashtags, phrases, topics)           │
│     ├─ Bot/spam filtering                                        │
│     └─ Deduplication (by ID and content hash)                    │
│                                                                   │
│  2. ANALYSIS (twitter_analyzer.py)                               │
│     ├─ Sentiment analysis (VADER + TextBlob ensemble)            │
│     ├─ Emotion detection (8 emotions via lexicon)                │
│     ├─ Topic classification (8 categories)                       │
│     ├─ Toxicity detection                                        │
│     └─ TF-IDF clustering (prevents single-tweet bias)            │
│                                                                   │
│  3. AGGREGATION (twitter_service.py)                             │
│     ├─ Per-category insights with confidence scores              │
│     ├─ Engagement-weighted scoring                               │
│     ├─ Dominant/minority opinion extraction                      │
│     └─ LLM narrative generation (Groq)                           │
│                                                                   │
│  4. INTEGRATION (ai_service.py)                                  │
│     └─ summarize_twitter_insights() for bullet summaries         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. twitter_scraper.py

**Purpose**: Scrape tweets using Twitter API v2 with intelligent query building and filtering.

**Key Features**:

- Multi-query fan-out: Uses 3+ diverse queries per college (hashtags, phrases, topics)
- Bot/spam filtering: Removes promotional content, multiple links, excessive hashtags
- Deduplication: By tweet ID and content hash (MD5 of normalized text)
- Graceful fallback: Returns empty list if API key is missing (no crash)

**Query Strategy**:

```python
# For "IIT Bombay":
queries = [
    '"IIT Bombay"',
    '#iitbombay',
    '#iitb',
    '"iit bombay placements"',
    '"iit bombay hostel"',
    '"iit bombay campus"',
    # ... etc
]
```

**API Usage**:

```python
from services.twitter_scraper import fetch_college_tweets

tweets = await fetch_college_tweets(
    college_name="IIT Bombay",
    target_count=200  # Minimum tweets to fetch
)
# Returns: list[Tweet]
```

### 2. twitter_analyzer.py

**Purpose**: Multi-dimensional NLP analysis of scraped tweets.

**Analysis Dimensions**:

1. **Sentiment Analysis** (VADER + TextBlob ensemble)
   - Compound score: -1 (negative) to +1 (positive)
   - Label: positive/negative/neutral
   - Engagement-weighted aggregation

2. **Emotion Detection** (8 emotions via keyword lexicon)
   - joy, anger, fear, sadness, surprise, disgust, trust, anticipation
   - Normalized scores [0, 1]

3. **Topic Classification** (8 categories)
   - placements, hostel_life, academics, coding_culture
   - peer_pressure, startup_culture, faculty, fest_campus_life

4. **Toxicity Detection**
   - Keyword-based heuristic
   - Filters toxic tweets from representative samples

5. **Embedding Clustering** (TF-IDF + KMeans)
   - Groups similar tweets into clusters
   - Minimum cluster size: 5 tweets
   - Prevents single-tweet bias in summaries

**API Usage**:

```python
from services.twitter_analyzer import analyse_college_tweets

report = analyse_college_tweets(
    college_name="IIT Bombay",
    tweets=tweets  # list[Tweet] from scraper
)
# Returns: TwitterAnalysisReport
```

### 3. twitter_service.py

**Purpose**: High-level orchestration with caching and LLM narrative generation.

**Key Features**:

- In-memory caching (24-hour TTL)
- Batch processing with concurrency control
- LLM narrative generation using Groq
- JSON serialization for API responses

**API Usage**:

```python
from services.twitter_service import get_twitter_insights

result = await get_twitter_insights(
    college_name="IIT Bombay",
    target_tweet_count=200,
    use_cache=True,
    generate_narrative=True
)
# Returns: dict with full analysis report
```

**Response Structure**:

```json
{
  "college_name": "IIT Bombay",
  "sample_size": 215,
  "overall": {
    "sentiment_score": 0.342,
    "sentiment_label": "positive",
    "positive_ratio": 0.65,
    "negative_ratio": 0.2,
    "neutral_ratio": 0.15,
    "confidence": 0.82,
    "top_emotions": ["joy", "trust", "anticipation"],
    "toxicity_rate": 0.03,
    "verified_tweet_ratio": 0.12
  },
  "opinions": {
    "dominant": "IIT Bombay placements are amazing! Got placed at Google...",
    "minority": "Hostel food quality needs improvement..."
  },
  "categories": {
    "placements": {
      "tweet_count": 45,
      "sentiment_score": 0.68,
      "sentiment_label": "positive",
      "confidence": 0.85,
      "representative_tweets": ["..."]
    }
    // ... other categories
  },
  "summary": "Based on 215 tweets, student sentiment toward IIT Bombay is predominantly positive (65% positive, 20% negative). Students speak most positively about placements. Confidence: 82%.",
  "data_quality_note": "Good sample size (215 tweets). Results are reasonably reliable."
}
```

### 4. ai_service.py Integration

**New Function**: `summarize_twitter_insights()`

**Purpose**: Generate 3 concise bullets from top tweets (by engagement).

**Features**:

- Sorts tweets by engagement score: `likes + 2 × retweets`
- Takes top 10 tweets for summarization
- Prompts Groq to identify:
  1. Most common sentiment (with "Mixed opinions" if divided)
  2. Specific placement companies mentioned
  3. Red flags raised by multiple users (not just one)

**API Usage**:

```python
from services.ai_service import summarize_twitter_insights

tweets = [
    {"text": "...", "likes": 150, "retweets": 45},
    # ... more tweets
]

bullets = await summarize_twitter_insights("IIT Bombay", tweets)
# Returns: list[str] with 3 bullets
```

**Example Output**:

```
• Mixed opinions: 80% positive on placements, 20% critical of facilities
• Companies mentioned: Google, Microsoft, Amazon, Goldman Sachs
• Red flag: Multiple users report poor hostel food quality
```

## Configuration

### Environment Variables (.env)

```bash
# Twitter API v2 Bearer Token (optional — service degrades gracefully if absent)
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Target tweet count per college (default: 200)
TWITTER_TARGET_TWEETS=200

# Cache TTL in seconds (default: 86400 = 24 hours)
TWITTER_CACHE_TTL_SECONDS=86400
```

### Getting a Twitter API Key

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app (Free tier: 500K tweets/month read access)
3. Generate Bearer Token
4. Add to `.env` file

**Without API Key**: Service returns empty results gracefully (no crash).

## Dependencies

Install via `pip install -r requirements.txt`:

```
tweepy>=4.14.0              # Twitter API v2 client
vaderSentiment>=3.3.2       # Sentiment analysis
textblob>=0.18.0            # Sentiment analysis (fallback)
scikit-learn>=1.4.0         # TF-IDF clustering
numpy>=1.26.0               # Numerical operations
beautifulsoup4>=4.12.0      # HTML parsing (for fallback scraping)
```

## Design Principles

### 1. No Single-Tweet Bias

**Problem**: A single viral tweet can skew perception.

**Solution**:

- Minimum cluster size: 5 tweets
- Only clusters with ≥5 tweets influence the summary
- Engagement-weighted aggregation (popular tweets count more)

### 2. Realistic Summaries

**Problem**: LLMs can hallucinate or over-generalize from limited data.

**Solution**:

- Always mention sample size and confidence level
- Use hedging language for small samples (<50 tweets)
- Provide both dominant and minority opinions
- Include data quality notes

### 3. Graceful Degradation

**Problem**: API keys may be missing or rate-limited.

**Solution**:

- Check for API key before making requests
- Return empty results with warning (no crash)
- Log clear error messages
- Provide fallback mechanisms

### 4. Multi-Query Coverage

**Problem**: Single query misses relevant tweets.

**Solution**:

- Use 3+ diverse queries per college
- Include hashtags, phrases, and topic-specific terms
- Deduplicate across queries
- Paginate until target count is reached

## Testing

### Verification Script

```bash
python scripts/verify_twitter_implementation.py
```

Checks:

- ✅ All files exist
- ✅ All functions/classes defined
- ✅ Config fields present
- ✅ Dependencies listed
- ✅ Acceptance criteria implemented

### Full Test Suite

```bash
python scripts/test_twitter_service.py
```

Tests:

1. Fetch Twitter insights for a known college
2. Test `summarize_twitter_insights()` with mock data
3. Test graceful fallback with empty tweets
4. Verify acceptance criteria

## Acceptance Criteria

### ✅ Criterion 1: Graceful Fallback Without API Key

**Requirement**: Service falls back gracefully if `TWITTER_BEARER_TOKEN` is not set.

**Implementation**:

```python
# twitter_scraper.py
bearer_token = getattr(settings, "twitter_bearer_token", "")
if not bearer_token:
    logger.warning("TWITTER_BEARER_TOKEN not set. Twitter scraping unavailable.")
    return []
```

**Test**: Run without API key → returns empty list, no crash.

### ✅ Criterion 2: Engagement-Based Sorting

**Requirement**: With API key, returns tweets sorted by engagement score descending.

**Implementation**:

```python
# twitter_analyzer.py
engagement_score = likes + 2 * retweets
# Weighted aggregation in aggregate_category()
weight = 1 + math.log1p(tweet.likes + tweet.retweets)
```

**Test**: Verify high-engagement tweets appear first in representative samples.

### ✅ Criterion 3: Groq Summarization with Engagement Context

**Requirement**: Groq summarization prompt includes engagement-weighted tweet context.

**Implementation**:

```python
# ai_service.py - summarize_twitter_insights()
sorted_tweets = sorted(
    tweets,
    key=lambda t: t.get('likes', 0) + 2 * t.get('retweets', 0),
    reverse=True
)
top_tweets = sorted_tweets[:10]

for tweet in top_tweets:
    engagement = tweet.get('likes', 0) + 2 * tweet.get('retweets', 0)
    tweet_lines.append(f"[Engagement: {engagement}] {tweet['text']}")
```

**Test**: Verify prompt includes engagement scores for each tweet.

## Usage Examples

### Example 1: Basic Usage

```python
from services.twitter_service import get_twitter_insights

# Fetch and analyze tweets
result = await get_twitter_insights("IIT Bombay")

print(f"Sample size: {result['sample_size']}")
print(f"Sentiment: {result['overall']['sentiment_label']}")
print(f"Summary: {result['summary']}")
```

### Example 2: Batch Processing

```python
from services.twitter_service import get_twitter_insights_batch

colleges = ["IIT Bombay", "IIT Delhi", "NIT Trichy"]
results = await get_twitter_insights_batch(colleges, target_tweet_count=100)

for college, data in results.items():
    print(f"{college}: {data['overall']['sentiment_label']}")
```

### Example 3: Custom Summarization

```python
from services.ai_service import summarize_twitter_insights

tweets = [
    {"text": "Great placements!", "likes": 200, "retweets": 50},
    {"text": "Poor hostel food", "likes": 10, "retweets": 2},
]

bullets = await summarize_twitter_insights("IIT Bombay", tweets)
for bullet in bullets:
    print(bullet)
```

## Troubleshooting

### Issue: No tweets found

**Possible causes**:

1. `TWITTER_BEARER_TOKEN` not set → Add to `.env`
2. API rate limit exceeded → Wait 15 minutes
3. No recent tweets match queries → Try different college name
4. API tier doesn't support search → Upgrade to Basic tier ($100/month)

**Solution**: Check logs for specific error messages.

### Issue: Low confidence scores

**Possible causes**:

1. Small sample size (<50 tweets) → Increase `target_tweet_count`
2. Tweets are scattered across many clusters → Normal for mixed opinions
3. Many tweets filtered as spam → Review filtering rules

**Solution**: Increase target count or adjust filtering thresholds.

### Issue: Biased summaries

**Possible causes**:

1. Single viral tweet dominating → Clustering should prevent this
2. All tweets from same subreddit → Diversify queries
3. Bot tweets not filtered → Review bot detection patterns

**Solution**: Check `representative_tweets` in category insights.

## Future Enhancements

1. **Nitter Fallback**: Add public scraping fallback when API is unavailable
2. **Temporal Analysis**: Track sentiment changes over time
3. **Comparative Analysis**: Compare multiple colleges side-by-side
4. **Image Analysis**: Extract sentiment from tweet images
5. **Network Analysis**: Identify influential users and communities

## References

- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)
- [TextBlob Documentation](https://textblob.readthedocs.io/)
- [scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)

## License

Part of the Pathfinder project. See main README for license information.
