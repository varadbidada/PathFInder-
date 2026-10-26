# Pathfinder Class 12 System - Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Code Implementation

- [x] **Questions bank redesigned** (`data/questions_class12.json`)
  - 3 fixed opener questions
  - Stage templates with examples
  - Branch profiles with ideal traits
- [x] **Counsellor prompts created** (`services/counsellor_prompts.py`)
  - SYSTEM_PROMPT with rules
  - build_extraction_prompt()
  - build_confirmation_prompt()
  - build_retry_prompt()
  - get_branch_description()
  - build_fallback_question()

- [x] **StudentModel verified** (`models/student_model.py`)
  - 7 numeric traits
  - 3 categorical traits
  - 5 qualitative lists
  - EMA update logic
  - Branch scoring algorithm

- [x] **LLM engine redesigned** (`engines/adaptive_engine_llm.py`)
  - Fixed openers for turns 1-3
  - LLM contextual questions for turns 4+
  - Duplicate detection and retry
  - 5-stage progression
  - Completion logic

- [x] **Persistence updated** (`main.py`, middleware)
  - student_model_snapshot support
  - New /api/session/{id}/model endpoint

### 2. Testing

- [x] **Quick integration test**

  ```bash
  cd backend
  python quick_test.py
  ```

  Expected: All tests pass ✅

- [ ] **Full verification test**

  ```bash
  cd backend
  python test_class12_system.py
  ```

  Expected:
  - Branch hypothesis: Mech or ECE
  - Confidence > 0.4 after turn 6
  - High hands_on score
  - No duplicate questions

- [ ] **Manual API testing**
  - Start session
  - Send 3-5 chat messages
  - Check student model endpoint
  - Verify completion flow

### 3. LLM Configuration

- [x] **LLM availability checked**

  ```bash
  curl http://localhost:8080/api/llm-status
  ```

  Current: ✅ Ollama available (llama3.2:3b)

- [ ] **Groq API key set** (optional, for better quality)

  ```bash
  export GROQ_API_KEY=your_key_here
  ```

- [ ] **Verify LLM responses**
  - Questions are jargon-free
  - Questions are reactive
  - No duplicates generated

### 4. Database

- [ ] **MongoDB running**

  ```bash
  # Check connection
  curl http://localhost:8080/health
  ```

  Should show: `"mongodb": {"status": "connected"}`

- [ ] **Verify persistence**
  - Start a session
  - Send messages
  - Check MongoDB for chat records
  - Verify student_model_snapshot present

### 5. Documentation

- [x] **README created** (`CLASS12_REDESIGN_README.md`)
- [x] **Implementation summary** (`IMPLEMENTATION_SUMMARY.md`)
- [x] **Architecture diagram** (`SYSTEM_ARCHITECTURE.md`)
- [x] **Deployment checklist** (this file)

## 🚀 Deployment Steps

### Step 1: Pre-Deployment Testing

```bash
# 1. Run quick test
cd backend
python quick_test.py

# Expected output:
# ✅ StudentModel test passed
# ✅ Prompts test passed
# ✅ Engine initialization test passed
# ✅ LLM is available
# ✅ Single turn test passed
```

### Step 2: Start Backend Server

```bash
# Navigate to backend
cd backend

# Activate virtual environment (if using one)
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Start FastAPI server
python main.py

# Server should start on http://127.0.0.1:8080
```

### Step 3: Verify Health Endpoint

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "2.0.0",
  "active_sessions": 0,
  "mongodb": {
    "status": "connected",
    "database": "pathfinder_db"
  }
}
```

### Step 4: Test Session Flow

#### 4.1 Start Session

```bash
curl -X POST http://localhost:8080/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "jee_main",
    "jee_rank": 5000,
    "budget_lakh": 3
  }'
```

Expected:

```json
{
  "session_id": "...",
  "first_question": "If you had a completely free Saturday...",
  "message": "Hi! I'm Pathfinder..."
}
```

#### 4.2 Send First Answer

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<session_id_from_above>",
    "user_message": "I would probably spend it fixing my bicycle or taking apart old electronics"
  }'
```

Expected:

```json
{
  "session_id": "...",
  "assistant_message": "In school, which subject made you feel...",
  "next_question": "In school, which subject made you feel...",
  "branch_scores": {"CS": 0.5, "Mech": 0.5, ...},
  "overall_confidence": 0.0,
  "is_complete": false,
  "trait_breakdown": {...}
}
```

#### 4.3 Check Student Model (Debug)

```bash
curl http://localhost:8080/api/session/<session_id>/model
```

Expected:

```json
{
  "math_aptitude": 0.5,
  "hands_on": 0.5,
  "interests": [],
  "branch_hypothesis": "unknown",
  "hypothesis_confidence": 0.0,
  ...
}
```

### Step 5: Verify LLM Questions (Turn 4+)

Continue chatting until turn 4. Verify:

- [ ] Question is different from openers
- [ ] Question reacts to student's answers
- [ ] Question contains no jargon (DSA, API, circuits, etc.)
- [ ] Question is open-ended
- [ ] Student model is being updated

### Step 6: Complete Session

Continue until completion. Verify:

- [ ] Confidence increases over turns
- [ ] Branch hypothesis is set (not "unknown")
- [ ] Final report includes:
  - Recommended branch
  - Branch summary (simple language)
  - Top 3 branches
  - Trait breakdown

## 🧪 Testing Scenarios

### Scenario 1: Mechanical Engineering Student

**Answers:**

1. "I'd spend it fixing my bicycle or taking apart old radios"
2. "Physics was best — especially when we derived things from scratch"
3. "I want to build machines that help people"
4. "I love understanding how things work mechanically"
5. "I prefer hands-on experiments over reading theory"

**Expected:**

- Branch: Mech (high confidence)
- Traits: hands_on > 0.7, spatial_reasoning > 0.6
- Interests: ["machines", "building", "physics"]

### Scenario 2: Computer Science Student

**Answers:**

1. "I'd probably code a simple game or automate something on my computer"
2. "Math was best — I loved solving logical puzzles"
3. "I want to work on AI or build apps that millions use"
4. "I enjoy problem-solving more than physical work"
5. "I like the idea of creating digital products"

**Expected:**

- Branch: CS (high confidence)
- Traits: logical_thinking > 0.7, problem_solving > 0.7, hands_on < 0.4
- Interests: ["programming", "logic", "problem-solving"]

### Scenario 3: Uncertain Student

**Answers:**

1. "I don't know, maybe watch movies or sleep"
2. "I didn't really love any subject, they were all okay"
3. "My parents want me to do engineering but I'm not sure"

**Expected:**

- Branch: unknown or low confidence
- Multiple follow-up questions to probe deeper
- System should detect vague answers and ask more specific questions

## 📊 Monitoring

### Metrics to Track

1. **Session Completion Rate**
   - How many sessions reach completion?
   - Target: > 80%

2. **Confidence Progression**
   - Average confidence by turn number
   - Target: > 0.6 by turn 8

3. **Branch Distribution**
   - Which branches are most recommended?
   - Are all branches being recommended?

4. **Question Quality**
   - Duplicate rate: Target < 5%
   - LLM failure rate: Target < 10%

5. **Student Engagement**
   - Average answer length
   - Dropout rate by turn

### MongoDB Queries for Monitoring

```javascript
// Average confidence by turn
db.chats.aggregate([
  { $group: { _id: "$turn", avgConfidence: { $avg: "$confidence" } } },
  { $sort: { _id: 1 } },
]);

// Branch distribution
db.chats.aggregate([
  { $match: { category: "COMPLETED" } },
  {
    $group: {
      _id: "$student_model_snapshot.branch_hypothesis",
      count: { $sum: 1 },
    },
  },
]);

// Duplicate question check
db.chats.aggregate([
  { $group: { _id: "$question", count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } },
]);
```

## 🐛 Troubleshooting

### Issue: LLM not generating questions

**Symptoms:**

- All questions are from fixed openers
- No contextual questions after turn 3

**Check:**

```bash
curl http://localhost:8080/api/llm-status
```

**Fix:**

- Ensure Groq API key is set OR Ollama is running
- Check LLM client logs for errors
- Verify prompts are correctly formatted

### Issue: Duplicate questions

**Symptoms:**

- Same question asked multiple times
- Similar questions with slight rewording

**Check:**

- Is similarity threshold too low? (should be 0.7)
- Is retry logic working?

**Fix:**

- Check `_is_duplicate_question()` logic
- Increase similarity threshold
- Add more examples to retry prompt

### Issue: Low confidence even after many turns

**Symptoms:**

- Confidence stuck at < 0.4 after 8+ turns
- Branch hypothesis still "unknown"

**Check:**

- Student answers: Are they vague?
- LLM extractions: Are trait_updates null?
- EMA alpha: Is it too low?

**Fix:**

- Increase EMA alpha from 0.4 to 0.5
- Add more aggressive probing questions
- Lower confidence threshold for completion

### Issue: Student model not updating

**Symptoms:**

- All traits remain at 0.5
- Interests list is empty

**Check:**

- Is LLM returning trait_updates?
- Is apply_updates() being called?

**Fix:**

- Check LLM response parsing
- Verify JSON structure
- Add logging to apply_updates()

## 📝 Rollback Plan

If deployment fails:

1. **Revert to deterministic engine**

   ```bash
   # In main.py, force deterministic engine
   use_llm = False
   ```

2. **Use old questions.json**

   ```bash
   cp data/questions.json.backup data/questions.json
   ```

3. **Disable student_model_snapshot**
   ```python
   # In persistence_middleware.py
   student_model_snapshot = None
   ```

## ✅ Post-Deployment Verification

### Day 1

- [ ] Monitor health endpoint every hour
- [ ] Check MongoDB for new chat records
- [ ] Verify no errors in server logs
- [ ] Test 3-5 complete sessions manually

### Week 1

- [ ] Analyze branch distribution
- [ ] Check confidence progression
- [ ] Identify most common questions
- [ ] Review duplicate question rate

### Week 2

- [ ] Gather user feedback
- [ ] Fine-tune EMA alpha if needed
- [ ] Adjust confidence thresholds
- [ ] Add more stage templates if needed

## 🎯 Success Criteria

The deployment is successful if:

✅ **Functionality**

- Sessions complete without errors
- Questions are jargon-free
- Branch recommendations make sense
- Confidence increases over turns

✅ **Performance**

- < 3s average response time
- < 5% duplicate question rate
- > 80% session completion rate
- > 0.6 average final confidence

✅ **User Experience**

- Questions feel natural
- Students can answer without confusion
- Recommendations feel personalized
- No technical terms used

## 📞 Support

If issues arise:

1. Check server logs: `tail -f backend/logs/pathfinder.log`
2. Check MongoDB: `mongo pathfinder_db`
3. Review this checklist for troubleshooting steps
4. Consult documentation:
   - `CLASS12_REDESIGN_README.md`
   - `SYSTEM_ARCHITECTURE.md`
   - `IMPLEMENTATION_SUMMARY.md`

---

**Last Updated:** January 2025  
**Version:** 2.0.0  
**Status:** READY FOR DEPLOYMENT 🚀
