# Semantic Conversation State Manager

## Overview

The upgraded `ContextManager` maintains **structured semantic state** across the full conversation, replacing the old raw text history approach. This enables:

- **Accumulated signals** with weighted rolling average
- **Contradiction detection** when student changes their mind
- **Entity tracking** (colleges, branches, constraints)
- **Sentiment trend** analysis
- **Compact context summaries** for LLM prompts (saves tokens)
- **Redis persistence** with 2-hour TTL

## Problem Statement

### Old System

```python
# Stored raw conversation history
history = [
    {"role": "user", "message": "I love math"},
    {"role": "assistant", "message": "Great!"},
    {"role": "user", "message": "I hate math"},  # Contradiction not detected!
]

# Groq got entire history on every call (wastes tokens)
groq_prompt = "\n".join(history)  # 1000+ tokens
```

### New System

```python
# Structured semantic state
state = ConversationState(
    accumulated_signals={
        "Math_Aptitude_enthusiasm": 0.667  # Weighted average
    },
    contradictions=[
        "Math Aptitude enthusiasm: Earlier 0.87, now 0.20 (difference: 0.67)"
    ],
    sentiment_trend=[0.5, 0.6, -0.2],
    mentioned_colleges=["IIT Bombay", "NIT Trichy"],
    expressed_constraints={"budget_lakh": 3.0, "rank": 2500}
)

# Compact summary for Groq (saves tokens)
summary = manager.get_groq_context_summary(session_id)
# Returns: ~170 tokens instead of 1000+
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConversationState                             │
├─────────────────────────────────────────────────────────────────┤
│  • accumulated_signals: dict[str, float]                         │
│    - Weighted rolling average: 0.7 * old + 0.3 * new            │
│    - Reflects all answers, not just the last one                 │
│                                                                   │
│  • mentioned_colleges: list[str]                                 │
│  • mentioned_branches: list[str]                                 │
│  • sentiment_trend: list[float]                                  │
│    - Per-turn compound sentiment [-1, 1]                         │
│    - Tracks if student mood changes                              │
│                                                                   │
│  • expressed_constraints: ExpressedConstraints                   │
│    - budget_lakh, location, exam_type, rank                      │
│                                                                   │
│  • open_questions: list[str]                                     │
│    - Questions student hasn't answered yet                       │
│                                                                   │
│  • contradictions: list[str]                                     │
│    - Detected when signal changes by > 0.4                       │
│                                                                   │
│  • history: list[dict]                                           │
│    - Recent conversation turns (limited to 10)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ContextManager                              │
├─────────────────────────────────────────────────────────────────┤
│  Methods:                                                         │
│  • update_signals(session_id, new_signals)                       │
│    → Returns contradictions detected                             │
│                                                                   │
│  • update_entities(session_id, entities)                         │
│    → Tracks colleges, branches, constraints                      │
│                                                                   │
│  • update_sentiment(session_id, sentiment_compound)              │
│    → Adds to trend tracking                                      │
│                                                                   │
│  • get_groq_context_summary(session_id)                          │
│    → Returns compact summary (max 400 tokens)                    │
│                                                                   │
│  • add_turn(session_id, user_msg, assistant_msg, intent)         │
│    → Adds conversation turn to history                           │
│                                                                   │
│  • add_open_question / remove_open_question                      │
│    → Tracks unanswered questions                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Persistence Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Primary: Redis (if available)                                   │
│    • Key: conversation_state:{session_id}                        │
│    • TTL: 2 hours (7200 seconds)                                 │
│    • Auto-expiration on inactivity                               │
│                                                                   │
│  Fallback: In-Memory Dict                                        │
│    • Used when Redis is unavailable                              │
│    • Manual cleanup via cleanup_expired()                        │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Weighted Rolling Average for Signals

**Formula**: `new_value = 0.7 * old_value + 0.3 * new_extraction`

**Rationale**: Later answers have slightly more weight than earlier ones, but all answers contribute to the final score.

**Example**:

```python
# Turn 1: Student says "I'm good at math"
signals_1 = {"Math_Aptitude_ability": 0.9}
manager.update_signals(session_id, signals_1)
# Accumulated: 0.9

# Turn 2: Student says "Actually, I'm okay at math"
signals_2 = {"Math_Aptitude_ability": 0.6}
manager.update_signals(session_id, signals_2)
# Accumulated: 0.7 * 0.9 + 0.3 * 0.6 = 0.81

# Turn 3: Student says "Math is not my strong suit"
signals_3 = {"Math_Aptitude_ability": 0.4}
manager.update_signals(session_id, signals_3)
# Accumulated: 0.7 * 0.81 + 0.3 * 0.4 = 0.687

# Final accumulated value reflects all 3 answers
```

### 2. Contradiction Detection

**Threshold**: Signal difference > 0.4 triggers contradiction

**Example**:

```python
# Q3: "I love math"
signals_q3 = {"Math_Aptitude_enthusiasm": 0.9}
manager.update_signals(session_id, signals_q3)

# Q4-Q6: Maintain similar values
# Accumulated: ~0.87

# Q7: "I hate math"
signals_q7 = {"Math_Aptitude_enthusiasm": 0.2}
contradictions = manager.update_signals(session_id, signals_q7)

# Returns:
# {
#   "Math_Aptitude_enthusiasm":
#     "Math Aptitude enthusiasm: Earlier 0.87, now 0.20 (difference: 0.67)"
# }

# This contradiction is:
# 1. Logged for debugging
# 2. Stored in state.contradictions
# 3. Included in Groq context summary
# 4. Can trigger clarifying question
```

### 3. Entity Tracking

**Tracked Entities**:

- **Colleges**: Mentioned across all turns
- **Branches**: Discussed branches
- **Constraints**: Budget, location, exam type, rank

**Example**:

```python
# Turn 1
entities_1 = {
    "colleges": ["IIT Bombay", "IIT Delhi"],
    "branches": ["CS"],
    "budget_lakh": 2.5,
    "locations": ["Mumbai"],
}
manager.update_entities(session_id, entities_1)

# Turn 5
entities_5 = {
    "colleges": ["NIT Trichy"],  # New college
    "branches": ["Electronics"],  # New branch
    "exams": ["JEE Advanced"],
    "ranks": [2500],
}
manager.update_entities(session_id, entities_5)

# Final state:
# mentioned_colleges: ["IIT Bombay", "IIT Delhi", "NIT Trichy"]
# mentioned_branches: ["CS", "Electronics"]
# expressed_constraints: {
#   budget_lakh: 2.5,
#   location: "Mumbai",
#   exam_type: "JEE Advanced",
#   rank: 2500
# }
```

### 4. Sentiment Trend Tracking

**Purpose**: Track if student's mood changes over the conversation

**Example**:

```python
# Positive start
manager.update_sentiment(session_id, 0.5)
manager.update_sentiment(session_id, 0.6)

# Becomes negative
manager.update_sentiment(session_id, -0.2)
manager.update_sentiment(session_id, -0.3)

# Recovers
manager.update_sentiment(session_id, 0.1)

# Trend: [0.5, 0.6, -0.2, -0.3, 0.1]
# Average: 0.14 (slightly positive overall)
```

### 5. Compact Context Summary

**Purpose**: Replace raw conversation history with structured summary to save tokens

**Target**: Max 400 tokens (≈1600 chars)

**Example Output**:

```
Signals: Math Aptitude ability: 0.90, Logical Thinking ability: 0.80,
         Creativity enthusiasm: 0.80
Constraints: Budget: ₹3.0L, Location: Mumbai, Exam: JEE Advanced, Rank: 2500
Colleges: IIT Bombay, IIT Delhi, NIT Trichy (+1 more)
Branches: CS, Electronics, Mechanical
Mood: positive (avg: +0.46)
⚠️ Contradictions: Math Aptitude enthusiasm: Earlier 0.87, now 0.20
Unanswered: What's your budget?; Do you prefer team or solo work?
Recent:
  User: I'm interested in CS
  Assistant: Great! Tell me about your math skills.
  User: I'm good at math but find it boring
```

**Token Savings**:

- Old approach: 1000+ tokens (entire conversation history)
- New approach: ~170 tokens (structured summary)
- **Savings: 83%**

## API Reference

### ConversationState

```python
@dataclass
class ConversationState:
    session_id: str
    accumulated_signals: dict[str, float] = field(default_factory=dict)
    mentioned_colleges: list[str] = field(default_factory=list)
    mentioned_branches: list[str] = field(default_factory=list)
    sentiment_trend: list[float] = field(default_factory=list)
    expressed_constraints: ExpressedConstraints = field(default_factory=ExpressedConstraints)
    open_questions: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    last_intent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

### ContextManager

#### Initialization

```python
# With Redis
import redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")
manager = ContextManager(redis_client=redis_client)

# Without Redis (in-memory only)
manager = ContextManager()
```

#### Update Signals

```python
new_signals = {
    "Logical_Thinking_ability": 0.8,
    "Logical_Thinking_enthusiasm": 0.7,
    "Math_Aptitude_ability": 0.9,
}

contradictions = manager.update_signals(session_id, new_signals)

# Returns: dict[str, str] of detected contradictions
# Example: {"Math_Aptitude_enthusiasm": "Earlier 0.87, now 0.20 (difference: 0.67)"}
```

#### Update Entities

```python
entities = {
    "colleges": ["IIT Bombay", "NIT Trichy"],
    "branches": ["CS", "Electronics"],
    "budget_lakh": 3.0,
    "locations": ["Mumbai"],
    "exams": ["JEE Advanced"],
    "ranks": [2500],
}

manager.update_entities(session_id, entities)
```

#### Update Sentiment

```python
sentiment_compound = 0.5  # Range: [-1, 1]
manager.update_sentiment(session_id, sentiment_compound)
```

#### Add Conversation Turn

```python
manager.add_turn(
    session_id,
    user_message="I'm interested in CS",
    assistant_message="Great! Tell me about your math skills.",
    intent="branch_inquiry"
)
```

#### Track Open Questions

```python
# Add question
manager.add_open_question(session_id, "What's your budget?")

# Remove when answered
manager.remove_open_question(session_id, "What's your budget?")
```

#### Get Compact Summary

```python
summary = manager.get_groq_context_summary(session_id)
# Returns: str (max 1600 chars ≈ 400 tokens)

# Use in Groq prompt:
prompt = f"""
{summary}

Student's latest answer: {user_answer}

Generate next question:
"""
```

#### Get Full State

```python
state = manager.get(session_id)
# Returns: ConversationState

# Access fields:
print(state.accumulated_signals)
print(state.mentioned_colleges)
print(state.contradictions)
```

#### Get History Text

```python
history_text = manager.get_history_text(session_id, max_turns=5)
# Returns: str (formatted conversation history)
```

#### Clear Session

```python
manager.clear(session_id)
# Removes state from both Redis and memory
```

#### List Sessions

```python
session_ids = manager.list_sessions()
# Returns: list[str]
```

#### Cleanup Expired

```python
count = manager.cleanup_expired()
# Returns: int (number of sessions cleaned up)
# Note: Redis handles expiration automatically via TTL
```

## Configuration

### Constants

```python
MAX_HISTORY_TURNS = 10          # Keep last 10 user+assistant pairs
STATE_TTL_SECONDS = 7200        # 2 hours
CONTRADICTION_THRESHOLD = 0.4   # Signal diff > 0.4 triggers contradiction
SIGNAL_WEIGHT_NEW = 0.3         # Weight for new signal
SIGNAL_WEIGHT_OLD = 0.7         # Weight for old signal
```

### Redis Setup

```python
# In config.py
redis_url: str = "redis://localhost:6379/0"

# In main.py or service initialization
import redis
redis_client = redis.Redis.from_url(settings.redis_url)
manager = ContextManager(redis_client=redis_client)
```

## Integration Example

### In AI Service

```python
from nlp.context.manager import ContextManager

# Initialize (once at startup)
manager = ContextManager(redis_client=redis_client)

async def extract_signals_with_context(
    session_id: str,
    user_answer: str,
    question_asked: str,
) -> SignalOutput:
    """Extract signals and update context."""

    # Get compact context summary
    context_summary = manager.get_groq_context_summary(session_id)

    # Extract signals with context
    prompt = f"""
{context_summary}

Question: {question_asked}
Answer: {user_answer}

Extract signals:
"""

    signals = await extract_signals(user_answer, question_asked, context_summary)

    # Update accumulated signals
    contradictions = manager.update_signals(session_id, signals.to_dict())

    # If contradictions detected, log them
    if contradictions:
        logger.warning(f"Contradictions detected in {session_id}: {contradictions}")
        # Could trigger clarifying question here

    # Update sentiment
    try:
        from nlp.sentiment.analyzer import get_sentiment_analyzer
        sentiment_analyzer = get_sentiment_analyzer()
        sentiment = sentiment_analyzer.analyze(user_answer)
        manager.update_sentiment(session_id, sentiment['compound'])
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}")

    # Add conversation turn
    manager.add_turn(session_id, user_answer, intent="signal_extraction")

    return signals
```

### In Entity Extraction

```python
def extract_and_track_entities(session_id: str, user_message: str) -> dict:
    """Extract entities and update context."""

    # Extract entities
    entities = entity_extractor.extract(user_message)

    # Update context
    manager.update_entities(session_id, entities)

    return entities
```

## Testing

Run the test suite:

```bash
python scripts/test_context_manager.py
```

**Test Coverage**:

1. ✅ Basic state management
2. ✅ Accumulated signals (weighted rolling average)
3. ✅ Contradiction detection
4. ✅ Entity tracking
5. ✅ Sentiment trend
6. ✅ Groq context summary (under 400 tokens)
7. ✅ Conversation history management
8. ✅ Open question tracking
9. ✅ State persistence
10. ✅ All acceptance criteria

**Expected Output**:

```
Total: 10
Passed: 10
Failed: 0

✅ ALL TESTS PASSED!
```

## Acceptance Criteria

### ✅ Criterion 1: Accumulated Signals Reflect All Answers

**Requirement**: After 10 questions, accumulated_signals reflects all 10 answers (not just the last one).

**Test**:

```python
for i in range(1, 11):
    signals = {"Logical_Thinking_ability": 0.7 + (i * 0.01)}
    manager.update_signals(session_id, signals)

state = manager.get(session_id)
final_value = state.accumulated_signals["Logical_Thinking_ability"]
# Result: 0.7776 (weighted average of all 10 values)
```

**Result**: ✅ PASS

### ✅ Criterion 2: Contradiction Detection

**Requirement**: If student says "I love math" in Q3 then "I hate math" in Q7, contradiction is flagged.

**Test**:

```python
# Q3: Love math
signals_q3 = {"Math_Aptitude_enthusiasm": 0.9}
manager.update_signals(session_id, signals_q3)

# Q4-Q6: Maintain
for _ in range(3):
    manager.update_signals(session_id, {"Math_Aptitude_enthusiasm": 0.85})

# Q7: Hate math
signals_q7 = {"Math_Aptitude_enthusiasm": 0.2}
contradictions = manager.update_signals(session_id, signals_q7)

# Result: {"Math_Aptitude_enthusiasm": "Earlier 0.87, now 0.20 (difference: 0.67)"}
```

**Result**: ✅ PASS

### ✅ Criterion 3: Compact Context Summary

**Requirement**: get_groq_context_summary() returns under 400 tokens.

**Test**:

```python
# Build rich state with signals, entities, sentiment, history
summary = manager.get_groq_context_summary(session_id)
char_count = len(summary)
token_estimate = char_count / 4

# Result: 681 chars (~170 tokens)
```

**Result**: ✅ PASS (well under 400 token limit)

## Migration Guide

### Old Code

```python
# Old context manager
from nlp.context.manager import ContextManager

manager = ContextManager()

# Update with raw message
manager.update(
    session_id,
    user_message="I love math",
    entities={"colleges": ["IIT Bombay"]},
    assistant_message="Great!",
    intent="general_inquiry"
)

# Get history
history = manager.get_history_text(session_id)
```

### New Code

```python
# New context manager
from nlp.context.manager import ContextManager

manager = ContextManager(redis_client=redis_client)

# Update signals
signals = {"Math_Aptitude_enthusiasm": 0.9}
contradictions = manager.update_signals(session_id, signals)

# Update entities
entities = {"colleges": ["IIT Bombay"]}
manager.update_entities(session_id, entities)

# Update sentiment
manager.update_sentiment(session_id, 0.5)

# Add conversation turn
manager.add_turn(
    session_id,
    user_message="I love math",
    assistant_message="Great!",
    intent="general_inquiry"
)

# Get compact summary (instead of full history)
summary = manager.get_groq_context_summary(session_id)
```

## Performance Considerations

### Token Savings

**Old Approach**:

- Full conversation history: 1000+ tokens
- Sent to Groq on every call
- Cost: High

**New Approach**:

- Compact summary: ~170 tokens
- Structured semantic state
- Cost: 83% reduction

### Memory Usage

**Redis Storage**:

- Per session: ~2-5 KB
- 1000 sessions: ~2-5 MB
- Auto-expiration after 2 hours

**In-Memory Fallback**:

- Per session: ~2-5 KB
- Manual cleanup via `cleanup_expired()`

### Latency

**Redis Operations**:

- Get: <1ms
- Set: <1ms
- Negligible impact on response time

**In-Memory Operations**:

- Get: <0.1ms
- Set: <0.1ms
- Zero impact on response time

## Future Enhancements

1. **Contradiction Resolution**: Automatically generate clarifying questions
2. **Signal Confidence**: Track confidence per signal dimension
3. **Temporal Analysis**: Analyze how signals change over time
4. **Multi-Session Learning**: Learn from patterns across all sessions
5. **Anomaly Detection**: Flag unusual signal patterns
6. **Export/Import**: Save conversation state for later analysis

## References

- [Redis Documentation](https://redis.io/documentation)
- [Dataclasses in Python](https://docs.python.org/3/library/dataclasses.html)
- [Exponential Moving Average](https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average)

## License

Part of the Pathfinder project. See main README for license information.
