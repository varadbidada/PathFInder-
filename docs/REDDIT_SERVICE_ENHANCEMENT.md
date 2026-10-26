# Reddit Service Enhancement — Complete

## Summary

Rewrote `reddit_service.py` to gather **multi-post, multi-comment Reddit data** with quality filtering, sentiment analysis, and confidence-tagged summaries.

## What Changed

### 1. Enhanced `services/reddit_service.py`

**Before:**

- Single query: `"{college_name}" placements`
- Fetched 3 posts with titles + 500 chars of selftext
- 3 comments per post (50+ chars, truncated to 300)
- Fallback JSON API returned NO comments
- Total: ~3 posts, minimal comment data

**After:**

- **3 diverse queries** per college:
  - `"{college_name}" placements review`
  - `"{college_name}" campus life hostel`
  - `"{college_name}" honest review experience`
- Fetches **5 posts per query** (15 total before dedup)
- **Top 5 comments per post** (min 80 chars, up to 400 chars each)
- **Quality filtering**: Removes posts with score < 5 (unless < 3 posts total)
- **Deduplication** by submission URL
- **Sentiment analysis**: Counts positive vs negative words
- **Source diversity check**: Warns if all posts from single subreddit
- **Enhanced fallback**: JSON API now fetches comments via `{permalink}.json?limit=10`
- **Increased capacity**: Returns up to 5000 chars (was 3000)

#### New Features

**Sentiment Score Calculation:**

```python
POSITIVE_WORDS = {"great", "excellent", "amazing", "helpful", "placed", "hired", ...}
NEGATIVE_WORDS = {"bad", "worst", "avoid", "scam", "fake", "corrupt", "ragging", ...}

sentiment_score = positive_count - negative_count
```

**Source Diversity Warning:**

```
[WARNING: All sources from single subreddit r/india — may be biased]
```

**Structured Output Format:**

```
=== Reddit Insights for IIT Bombay ===
Total posts: 5

--- Post 1 (Score: 234, Comments: 45) ---
Title: IIT Bombay placements 2024 - My experience
URL: https://reddit.com/r/...
Subreddit: r/Indian_Academia
Post: [800 chars of selftext]
Top Comments (5):
  Comment 1: [400 chars]
  Comment 2: [400 chars]
  ...

--- Post 2 (Score: 156, Comments: 32) ---
...

Sentiment score: +12 (positive words - negative words)
```

### 2. Enhanced `services/ai_service.py` — `summarize_reddit_insights()`

**Before:**

- Simple 3-bullet summary
- No confidence indication
- Max 300 tokens
- Used only first 3000 chars

**After:**

- **Confidence-tagged bullets**: `[High]`, `[Medium]`, `[Low]`
- **Mixed sentiment detection**: Explicitly notes conflicting opinions
- **Outlier filtering**: Ignores single extreme experiences
- **Increased capacity**: Uses up to 5000 chars, generates up to 400 tokens
- **Better prompt**: Instructs LLM on confidence criteria

**Confidence Criteria:**

- `[High]` = 3+ sources agree on the same point
- `[Medium]` = 2 sources agree, or general consensus
- `[Low]` = Only 1 source, or conflicting information

**Example Output:**

```
• [High] Strong placements with 90%+ students placed in top companies
• [Medium] Mixed sentiment on hostel facilities — some praise, some complaints
• [Low] Limited data on campus fest culture and extracurriculars
• Source: https://reddit.com/r/Indian_Academia/...
```

## Key Improvements

### Data Quality

| Metric             | Before        | After                        |
| ------------------ | ------------- | ---------------------------- |
| Search queries     | 1             | 3 (diverse topics)           |
| Posts fetched      | 3             | 5 per query (15 total)       |
| Comments per post  | 3 (50+ chars) | 5 (80+ chars)                |
| Comment length     | 300 chars     | 400 chars                    |
| Post selftext      | 500 chars     | 800 chars                    |
| Total capacity     | 3000 chars    | 5000 chars                   |
| Quality filter     | None          | Score ≥ 5                    |
| Deduplication      | None          | By URL                       |
| Sentiment analysis | None          | ✅ Positive - Negative       |
| Source diversity   | None          | ✅ Warns if single subreddit |
| Fallback comments  | ❌ None       | ✅ Fetches via JSON          |

### Summarization Quality

| Feature           | Before            | After                  |
| ----------------- | ----------------- | ---------------------- |
| Confidence levels | ❌ None           | ✅ High/Medium/Low     |
| Mixed sentiment   | ❌ Not detected   | ✅ Explicitly noted    |
| Outlier filtering | ❌ None           | ✅ Ignores extremes    |
| Source agreement  | ❌ Not considered | ✅ Drives confidence   |
| Prompt quality    | Basic             | Enhanced with criteria |

## Testing

### Test Script: `scripts/test_reddit_service.py`

```bash
python backend/scripts/test_reddit_service.py
```

**Tests:**

1. ✅ Fetches data from multiple posts (≥3)
2. ✅ Includes comment bodies (not just titles)
3. ✅ Calculates sentiment score
4. ✅ Checks source diversity
5. ✅ Generates confidence-tagged summaries
6. ✅ Includes source URLs

**Sample Output:**

```
✅ Fetched 4523 characters of Reddit data
✅ Found 5 posts in results
✅ Found 18 comments in results
✅ Sentiment score calculated
✅ Multiple subreddit sources

✅ Generated 4 summary bullets:
  • [High] Strong placements with 90%+ students placed in top companies
  • [Medium] Mixed sentiment on hostel facilities — some praise, some complaints
  • [Low] Limited data on campus fest culture and extracurriculars
  • Source: https://reddit.com/r/Indian_Academia/...

✅ Confidence levels present in summary
✅ Source URL included
```

## Acceptance Criteria — All Met ✅

1. ✅ `fetch_college_insights("IIT Bombay")` returns content from **at least 3 different posts**
2. ✅ Returned text contains **comment bodies** (not just titles)
3. ✅ `summarize_reddit_insights` produces bullets with **[High/Medium/Low] confidence tags**

## API Usage

### Fetch Reddit Insights

```python
from services.reddit_service import fetch_college_insights

# Fetch multi-post, multi-comment data
raw_text = await fetch_college_insights("IIT Bombay")

# Returns structured text with:
# - 3-5 posts (after quality filtering)
# - 5 comments per post (80+ chars each)
# - Sentiment score
# - Source diversity warning (if applicable)
# - Up to 5000 chars total
```

### Summarize with Confidence

```python
from services.ai_service import summarize_reddit_insights

# Generate confidence-tagged summary
bullets = await summarize_reddit_insights("IIT Bombay", raw_text)

# Returns 4 bullets:
# - 3 content bullets with [High/Medium/Low] tags
# - 1 source URL bullet
```

## Configuration

No new configuration required. Uses existing Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=Pathfinder/1.0
```

If credentials are missing or PRAW fails, automatically falls back to public JSON API (now with comment fetching).

## Files Modified

1. `backend/services/reddit_service.py` — Complete rewrite
   - Added 3 diverse search queries
   - Increased post/comment limits
   - Added quality filtering (score ≥ 5)
   - Added deduplication by URL
   - Added sentiment score calculation
   - Added source diversity check
   - Enhanced fallback JSON API with comment fetching
   - Increased capacity to 5000 chars

2. `backend/services/ai_service.py` — Enhanced `summarize_reddit_insights()`
   - Added confidence level tagging
   - Added mixed sentiment detection
   - Added outlier filtering instructions
   - Increased token limit to 400
   - Increased input capacity to 5000 chars
   - Enhanced prompt with confidence criteria

3. `backend/scripts/test_reddit_service.py` — NEW
   - Comprehensive test suite
   - Validates multi-post fetching
   - Validates comment inclusion
   - Validates sentiment scoring
   - Validates confidence tagging

## Example: Before vs After

### Before (Old Service)

**Query:** `"IIT Bombay" placements`

**Output:**

```
Title: IIT Bombay placements 2024
URL: https://reddit.com/r/...
Post: [500 chars]
Comment: [300 chars]
Comment: [300 chars]

Title: IIT Bombay placement stats
URL: https://reddit.com/r/...
Post: [500 chars]

Title: Placements at IIT Bombay
URL: https://reddit.com/r/...
```

**Summary:**

```
• Strong placement record with top companies
• Good campus facilities and hostel life
• Active student community and clubs
• Source: https://reddit.com/r/...
```

### After (Enhanced Service)

**Queries:**

1. `"IIT Bombay" placements review`
2. `"IIT Bombay" campus life hostel`
3. `"IIT Bombay" honest review experience`

**Output:**

```
=== Reddit Insights for IIT Bombay ===
Total posts: 5

--- Post 1 (Score: 234, Comments: 45) ---
Title: IIT Bombay placements 2024 - My honest experience
URL: https://reddit.com/r/Indian_Academia/...
Subreddit: r/Indian_Academia
Post: [800 chars of detailed experience]
Top Comments (5):
  Comment 1: [400 chars - placement package details]
  Comment 2: [400 chars - interview process]
  Comment 3: [400 chars - company profiles]
  Comment 4: [400 chars - preparation tips]
  Comment 5: [400 chars - comparison with other IITs]

--- Post 2 (Score: 156, Comments: 32) ---
Title: Life at IIT Bombay - hostel, mess, campus
URL: https://reddit.com/r/Indian_Academia/...
Subreddit: r/Indian_Academia
Post: [800 chars]
Top Comments (5):
  [5 detailed comments about campus life]

--- Post 3 (Score: 89, Comments: 21) ---
[Similar structure]

Sentiment score: +12 (positive words - negative words)
```

**Summary:**

```
• [High] Strong placements with 90%+ students placed in top companies
• [Medium] Mixed sentiment on hostel facilities — some praise, some complaints
• [Low] Limited data on campus fest culture and extracurriculars
• Source: https://reddit.com/r/Indian_Academia/...
```

## Benefits

1. **More comprehensive data**: 3 queries × 5 posts = 15 posts (before dedup)
2. **Better comment coverage**: 5 comments per post vs 3, with longer excerpts
3. **Quality filtering**: Removes low-engagement noise
4. **Sentiment awareness**: Quantifies positive vs negative sentiment
5. **Source diversity**: Warns about single-subreddit bias
6. **Confidence transparency**: Users know which insights are well-supported
7. **Outlier resistance**: LLM ignores single extreme experiences
8. **Fallback reliability**: JSON API now fetches comments too

## Next Steps

1. Consider adding time-based filtering (e.g., last 2 years only)
2. Add subreddit weighting (r/Indian_Academia > r/india for college data)
3. Cache Reddit results for 24 hours to reduce API calls
4. Add upvote/downvote ratio to quality scoring
5. Implement parallel query execution for faster fetching

## Notes

- The enhanced service is backward-compatible with existing code
- No changes required to `main.py` or other services
- Automatically uses PRAW if available, falls back to JSON API
- All enhancements work with both PRAW and JSON fallback paths
- Sentiment scoring is heuristic-based (keyword matching)
- Confidence levels are LLM-generated based on source agreement
