# New Branch Scoring System - Redesigned

## Date: May 14, 2026

---

## What Changed

### ❌ OLD SYSTEM (Removed):

- Used **cumulative signals** with weighted average (70% old + 30% new)
- Signals accumulated across messages with exponential moving average
- More complex, harder to understand

### ✅ NEW SYSTEM (Current):

- Uses **simple average** of all signals in current session
- Each session is completely independent
- No memory across sessions
- Simpler, more predictable

---

## How It Works Now

### Within a Single Session

**Example Conversation**:

```
Message 1: "I love coding"
→ Signals: {Logical_Thinking_enthusiasm: 0.9, Math_Aptitude_enthusiasm: 0.6}

Message 2: "I hate math"
→ Signals: {Logical_Thinking_enthusiasm: 0.9, Math_Aptitude_enthusiasm: 0.1}

Message 3: "I enjoy problem solving"
→ Signals: {Logical_Thinking_enthusiasm: 0.95, Problem_Solving_enthusiasm: 0.9}

Aggregated Signals (used for branch scoring):
- Logical_Thinking_enthusiasm: (0.9 + 0.9 + 0.95) / 3 = 0.92
- Math_Aptitude_enthusiasm: (0.6 + 0.1) / 2 = 0.35
- Problem_Solving_enthusiasm: 0.9 / 1 = 0.9

Branch Scores calculated from these aggregated signals
```

### Across Multiple Sessions

```
SESSION 1:
- User says: "I love CS"
- Aggregated signals: {Logical_Thinking_enthusiasm: 0.9, ...}
- Branch scores: CS = 0.85

[User clicks Restart]

SESSION 2:
- New session ID generated
- user_responses = [] (EMPTY!)
- User says: "I love Mechanical"
- Aggregated signals: {Manual_Work_enthusiasm: 0.9, ...}
- Branch scores: Mechanical = 0.85
- NO MEMORY of Session 1!
```

---

## Key Differences

| Feature                    | OLD System                                       | NEW System                                |
| -------------------------- | ------------------------------------------------ | ----------------------------------------- |
| **Aggregation Method**     | Exponential moving average (70% old + 30% new)   | Simple average of all values              |
| **Memory Across Sessions** | Could leak if not properly reset                 | Impossible - each session independent     |
| **Complexity**             | Higher (weighted formula)                        | Lower (simple average)                    |
| **Predictability**         | Less predictable (recent messages weighted more) | More predictable (all messages equal)     |
| **Storage**                | `cumulative_signals` dict                        | No separate storage, calculated on-demand |

---

## Implementation Details

### Files Modified

1. **`backend/engines/conversation_fsm.py`**:
   - ❌ Removed: `cumulative_signals` field
   - ❌ Removed: `update_cumulative_signals()` method

2. **`backend/engines/conversation_controller.py`**:
   - ✅ Added: `_aggregate_session_signals()` method
   - ✅ Changed: Now aggregates signals from all responses in current session
   - ✅ Changed: Calculates simple average instead of weighted average

### New Aggregation Method

```python
def _aggregate_session_signals(self, state: ConversationState) -> Dict[str, float]:
    """
    Aggregate signals from all responses in the CURRENT session.
    Uses simple average of all signal values.
    """
    if not state.user_responses:
        return {}

    # Collect all signals from all responses
    signal_values: Dict[str, List[float]] = {}

    for response in state.user_responses:
        signals = response.get("signals", {})
        for key, value in signals.items():
            if key not in signal_values:
                signal_values[key] = []
            signal_values[key].append(value)

    # Calculate average for each signal
    aggregated = {}
    for key, values in signal_values.items():
        if values:
            aggregated[key] = sum(values) / len(values)

    return aggregated
```

---

## Benefits of New System

### 1. ✅ No Memory Leaks

- Each session starts with empty `user_responses`
- Impossible for previous session data to leak
- Guaranteed isolation

### 2. ✅ Simpler Logic

- Simple average is easier to understand
- No complex weighted formulas
- Easier to debug and maintain

### 3. ✅ Predictable Behavior

- All messages in a session have equal weight
- No "recent bias" from weighted average
- More transparent to users

### 4. ✅ Better Testing

- Easier to write unit tests
- Easier to verify correctness
- Easier to explain to stakeholders

---

## How Signals Are Stored

### ConversationState Structure

```python
@dataclass
class ConversationState:
    session_id: str
    user_responses: List[Dict[str, Any]] = [
        {
            "message": "I love coding",
            "signals": {
                "Logical_Thinking_enthusiasm": 0.9,
                "Math_Aptitude_enthusiasm": 0.6,
                ...
            }
        },
        {
            "message": "I hate math",
            "signals": {
                "Logical_Thinking_enthusiasm": 0.9,
                "Math_Aptitude_enthusiasm": 0.1,
                ...
            }
        },
        ...
    ]
```

### When Branch Scores Are Calculated

```python
# In conversation_controller.py, process_message():

# 1. Extract signals from current message
signals = await extract_signals(user_message, ...)

# 2. Store in user_responses
state.user_responses.append({
    "message": user_message,
    "signals": signals.to_dict(),
})

# 3. Aggregate ALL signals from ALL responses in THIS session
aggregate_signals = self._aggregate_session_signals(state)

# 4. Calculate branch scores from aggregated signals
result = evaluate(aggregate_signals, ...)

# 5. Update branch scores
state.update_branch_scores(result.normalized_scores)
```

---

## Testing

### Run Automated Test

```bash
cd backend
python scripts/test_new_scoring.py
```

**Expected Output**:

```
✅ Signals aggregate within a session (simple average)
✅ New sessions start with NO memory of previous sessions
✅ Empty sessions handled correctly
```

### Manual Test

**Test 1: Within-Session Aggregation**

1. Start session
2. Say: "I love coding" → Note CS score
3. Say: "I hate math" → CS score should adjust (average of both)
4. Say: "I enjoy problem solving" → CS score reflects all 3 messages

**Test 2: Cross-Session Isolation**

1. Session 1: Say "I love CS" → Complete
2. Click **🔄 Restart**
3. Session 2: Say "I love Mechanical" → Complete
4. Verify: NO CS preference in Session 2

---

## Verification

### Check Backend Logs

Look for these patterns:

```json
{"level": "INFO", "message": "Session <uuid>: Aggregated signals from 3 messages"}
{"level": "DEBUG", "message": "Aggregated 16 signals from 3 responses"}
{"level": "INFO", "message": "Session <uuid>: Branch scores - {'CS': 0.75, ...}"}
```

### Check Session State

```python
# In Python console
from engines.session_manager import session_manager

state = session_manager.get_session("your-session-id")
print(f"Total responses: {len(state.user_responses)}")
print(f"Branch scores: {state.branch_scores}")
```

---

## Migration Notes

### What Was Removed

1. ❌ `cumulative_signals` field from `ConversationState`
2. ❌ `update_cumulative_signals()` method
3. ❌ Exponential moving average logic
4. ❌ Weighted average formula (70% old + 30% new)

### What Was Added

1. ✅ `_aggregate_session_signals()` method
2. ✅ Simple average calculation
3. ✅ Better logging for aggregation

### Backward Compatibility

- ✅ No breaking changes to API
- ✅ No changes to frontend
- ✅ No changes to database schema (we use in-memory storage)
- ✅ Existing sessions will work (they just won't have cumulative_signals)

---

## Summary

✅ **Redesigned branch scoring system**  
✅ **Removed cumulative signals (no memory across sessions)**  
✅ **Uses simple average of all responses in current session**  
✅ **Each session is completely independent**  
✅ **Simpler, more predictable, easier to maintain**  
✅ **All tests passing**

**Key Point**: Each new session starts with a clean slate. No memory of previous sessions!

---

## If You Still See Old Data

If you're still seeing recommendations from previous sessions:

1. **Restart the backend server** (to load new code)
2. **Click the 🔄 Restart button** (to delete old session)
3. **Clear browser cache** (to remove any cached data)
4. **Check backend logs** (to verify new session ID)

The new system makes it **impossible** for data to leak across sessions because:

- Each session has its own `user_responses` list
- Aggregation only looks at current session's responses
- New session = empty `user_responses` = no signals = no scores
