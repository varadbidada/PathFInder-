# Sentiment Analysis Module

Real sentiment analysis for student answers and social media content.

## Quick Start

```python
from nlp.sentiment.analyzer import get_sentiment_analyzer
from nlp.sentiment.cross_verify import get_cross_verification_engine

# Analyze sentiment
analyzer = get_sentiment_analyzer()
result = analyzer.analyze("I hate math but I'm decent at it")
print(result)
# {"compound": -1.0, "positive": 0.0, "negative": 1.0, "neutral": 0.0, "method": "lexicon"}

# Cross-verify multiple sources
engine = get_cross_verification_engine()
scores = [0.7, 0.8, 0.75, -0.9, 0.72]  # -0.9 is outlier
verification = engine.verify(scores)
print(verification)
# {"consensus_sentiment": "positive", "confidence": "high", "outliers_removed": 1, ...}
```

## Features

### SentimentAnalyzer

- **Multi-strategy**: Transformers → VADER → Domain Lexicon
- **Negation handling**: "not good at math" → negative
- **Intensifiers**: "very good" → stronger positive
- **Diminishers**: "kind of good" → weaker positive
- **Domain-aware**: Understands "good at", "bad at", "struggle with"

### CrossVerificationEngine

- **Outlier detection**: Removes extreme sentiment posts
- **Consensus classification**: positive/mixed/negative
- **Confidence scoring**: high/medium/low
- **Mixed opinion detection**: Warns when sentiment varies

## Files

- `analyzer.py` — Multi-strategy sentiment analyzer
- `cross_verify.py` — Cross-verification engine
- `domain_lexicon.json` — Domain-specific sentiment lexicon
- `__init__.py` — Module exports

## Testing

```bash
python backend/scripts/test_sentiment_analysis.py
```

## Integration

### Student Answers (Automatic)

Sentiment weighting is automatically applied in `services/ai_service.py`:

- Negative sentiment (< -0.3): multiply signals by 0.7
- Positive sentiment (> 0.5): multiply signals by 1.15

### Social Media (Automatic)

Sentiment analysis and cross-verification are automatically applied in `services/reddit_service.py`:

- Per-post sentiment tagging
- Outlier removal before summarization
- Consensus sentiment reporting

## Dependencies

**Required:**

- None (lexicon fallback always works)

**Optional (for better accuracy):**

- `vaderSentiment` — Fast, good for social media
- `transformers` + `torch` — Best accuracy (adds ~500MB)

## Examples

### Negative Sentiment Detection

```python
analyzer.analyze("I hate math but I'm decent at it")
# compound: -1.0 (negative)
```

### Positive Sentiment Detection

```python
analyzer.analyze("I absolutely love coding and solving algorithms!")
# compound: +1.0 (positive)
```

### Negation Handling

```python
analyzer.analyze("I'm not good at math")
# compound: 0.0 (neutral, negation flips "good" to negative)

analyzer.analyze("I don't hate programming")
# compound: -1.0 (negative, negation flips "hate" to positive)
```

### Outlier Removal

```python
engine = get_cross_verification_engine()
scores = [0.3, 0.25, 0.28, -0.9, 0.32]  # -0.9 is outlier
result = engine.verify(scores)
# outliers_removed: 1
# cleaned_scores: [0.3, 0.25, 0.28, 0.32]
```

## Configuration

No configuration required. The analyzer automatically selects the best available method:

1. **Transformers** (if installed) — Best accuracy
2. **VADER** (if installed) — Fast, good for social media
3. **Domain Lexicon** (always available) — Fallback with negation handling

## Performance

| Method       | Speed  | Accuracy | Memory |
| ------------ | ------ | -------- | ------ |
| Transformers | ~200ms | Highest  | ~500MB |
| VADER        | ~5ms   | High     | ~5MB   |
| Lexicon      | ~2ms   | Good     | <1MB   |

## Limitations

- English only (no multilingual support)
- Sarcasm not detected
- Short texts may lack context
- Domain-specific (tuned for education/career)

## See Also

- `SENTIMENT_ANALYSIS_INTEGRATION.md` — Full documentation
- `scripts/test_sentiment_analysis.py` — Test suite
- `services/ai_service.py` — Student answer integration
- `services/reddit_service.py` — Social media integration
