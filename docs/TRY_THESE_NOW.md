# 🚀 Try These Tests NOW!

## Server is Running: `http://127.0.0.1:8080`

---

## 🌐 Test 1: Open in Browser (EASIEST!)

### Interactive API Documentation

```
http://127.0.0.1:8080/docs
```

**What you'll see**:

- Full list of all API endpoints
- Click any endpoint → "Try it out" → Fill parameters → "Execute"
- See live responses!

**Try these endpoints first**:

1. `GET /health` - Check server health
2. `POST /session/start` - Start a counselling session
3. `POST /api/career-roadmap` - Get a 5-year career roadmap

---

## 💻 Test 2: Simple Browser Tests

### Health Check

Open in browser:

```
http://127.0.0.1:8080/health
```

**Expected**: JSON with status, timestamp, version

### List Branches

Open in browser:

```
http://127.0.0.1:8080/branches
```

**Expected**: List of 11 engineering branches

---

## 🎯 Test 3: Complete Counselling Flow (Copy-Paste)

### Step 1: Start Session

```bash
curl -X POST http://127.0.0.1:8080/session/start -H "Content-Type: application/json" -d "{\"jee_rank\": 5000, \"budget_lakh\": 5, \"preferred_location\": \"Bangalore\"}"
```

**Look for**: `"session_id": "..."`  
**Copy this session_id for next steps!**

---

### Step 2: Chat - CS Interest

**Replace YOUR_SESSION_ID with the actual ID from Step 1**

```bash
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\", \"user_message\": \"I love coding and solving algorithmic problems. Math is my favorite subject.\"}"
```

**Look for**: `"branch_scores"` - CS score should be high

---

### Step 3: Check Session State

```bash
curl http://127.0.0.1:8080/session/YOUR_SESSION_ID
```

**Look for**:

- `"rank": 5000`
- `"recommended_branch": "CS"` (or similar)
- `"overall_confidence": 0.XX`

---

## 🔥 Test 4: Novel Features (The Cool Stuff!)

### Feature 9A: What-If Simulator

**"What if I improve my rank from 10000 to 5000?"**

```bash
curl -X POST http://127.0.0.1:8080/api/what-if -H "Content-Type: application/json" -d "{\"current_rank\": 10000, \"target_rank\": 5000, \"branch\": \"CS\", \"rank_type\": \"jee_main\"}"
```

**Look for**:

- `"colleges_gained": [...]` - Better colleges you can get
- `"colleges_lost": [...]` - Colleges you'll lose
- Response time should be < 200ms

---

### Feature 9C: Placement Reality Check

**"What are the real placement stats for IIT Bombay?"**

```bash
curl -X POST http://127.0.0.1:8080/api/placement-reality -H "Content-Type: application/json" -d "{\"college_name\": \"IIT Bombay\", \"branch\": \"Computer Science\"}"
```

**Look for**:

- `"median_salary_lpa"` - What most students get
- `"headline_salary_lpa"` - Highest package (marketing number)
- `"inflation_ratio"` - How inflated the stats are
- `"is_inflated": true/false`

---

### Feature 9D: Career Roadmap

**"What's my 5-year career path for CS?"**

```bash
curl -X POST http://127.0.0.1:8080/api/career-roadmap -H "Content-Type: application/json" -d "{\"branch\": \"Computer Science\", \"college_tier\": \"Moderate\"}"
```

**Look for**:

- `"year_1"` - First year plan
- `"year_2_3"` - Second and third year
- `"year_4"` - Fourth year (placement prep)
- `"year_5"` - First job reality

---

### Feature 9B: Peer Comparison

**"What are other students choosing?"**

First, store a choice:

```bash
curl -X POST "http://127.0.0.1:8080/api/peer-choice?branch_predicted=CS&rank=5000&location=Bangalore&college_chosen=NIT+Trichy"
```

Then get stats:

```bash
curl "http://127.0.0.1:8080/api/peer-stats?branch=CS&rank=5000&location=Bangalore"
```

**Look for**:

- `"total_peers"` - How many students in your rank range
- `"branch_match_percentage"` - % who chose same branch
- `"message"` - Confidence booster message

---

## 🐍 Test 5: Run Automated Test Suite

```bash
cd "c:\Users\theva\OneDrive\Documents\4th sem\Pathfinder"
python test_pathfinder.py
```

**Expected**: All 11 tests pass with green checkmarks ✅

---

## 🎨 Test 6: Different Student Profiles

### Profile A: CS Enthusiast (High Rank)

```bash
# Start
curl -X POST http://127.0.0.1:8080/session/start -H "Content-Type: application/json" -d "{\"jee_rank\": 3000}"

# Chat (use session_id from above)
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\", \"user_message\": \"I code 5+ hours daily. I've built several web apps and love algorithms.\"}"
```

**Expected**: High CS score, Dream tier colleges (IITs, top NITs)

---

### Profile B: Mechanical Engineer (Medium Rank)

```bash
# Start
curl -X POST http://127.0.0.1:8080/session/start -H "Content-Type: application/json" -d "{\"jee_rank\": 15000}"

# Chat
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\", \"user_message\": \"I love working with my hands, fixing cars, and building machines.\"}"
```

**Expected**: High Mechanical score, Moderate tier colleges

---

### Profile C: Civil Engineer (Lower Rank)

```bash
# Start
curl -X POST http://127.0.0.1:8080/session/start -H "Content-Type: application/json" -d "{\"jee_rank\": 25000}"

# Chat
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\", \"user_message\": \"I enjoy designing structures and buildings. I'm creative and good at visualization.\"}"
```

**Expected**: High Civil score, Safe tier colleges

---

## 📊 What to Look For

### In Chat Responses:

- ✅ `branch_scores` - Should change based on your answers
- ✅ `overall_confidence` - Should increase with more answers
- ✅ `next_question` - Should ask relevant follow-up questions
- ✅ `assistant_message` - Should be conversational and natural

### In What-If Simulator:

- ✅ Response time < 200ms
- ✅ `colleges_gained` - Better colleges with improved rank
- ✅ `colleges_lost` - Colleges you'll lose access to

### In Placement Reality:

- ✅ `median_salary_lpa` vs `headline_salary_lpa` - Should be different
- ✅ `inflation_ratio` - Should be > 1.0 for most colleges
- ✅ `is_inflated` - Should be true if ratio > 3.0

### In Career Roadmap:

- ✅ All 4 stages present: `year_1`, `year_2_3`, `year_4`, `year_5`
- ✅ Realistic descriptions (not aspirational)
- ✅ Specific company names, salary ranges, skills

---

## 🎯 Quick Verification Checklist

Run these 5 commands in order:

```bash
# 1. Health check
curl http://127.0.0.1:8080/health

# 2. Start session (save session_id)
curl -X POST http://127.0.0.1:8080/session/start -H "Content-Type: application/json" -d "{\"jee_rank\": 5000}"

# 3. Chat (replace YOUR_SESSION_ID)
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\", \"user_message\": \"I love coding\"}"

# 4. What-If simulator
curl -X POST http://127.0.0.1:8080/api/what-if -H "Content-Type: application/json" -d "{\"current_rank\": 10000, \"target_rank\": 5000, \"branch\": \"CS\", \"rank_type\": \"jee_main\"}"

# 5. Career roadmap
curl -X POST http://127.0.0.1:8080/api/career-roadmap -H "Content-Type: application/json" -d "{\"branch\": \"Computer Science\", \"college_tier\": \"Moderate\"}"
```

**If all 5 work**: ✅ Everything is working perfectly!

---

## 🆘 Troubleshooting

### Command not working?

- Make sure server is running: `curl http://127.0.0.1:8080/health`
- Check you're using the correct session_id
- Try the browser method: `http://127.0.0.1:8080/docs`

### Getting 404 errors?

- Server might not be running
- Check port: Should be 8080, not 8000

### Getting validation errors?

- Check JSON syntax (quotes, commas)
- Make sure rank is between 1 and 1,000,000
- Make sure session_id is valid

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Health check returns `"status": "healthy"`
2. ✅ Session start returns a `session_id`
3. ✅ Chat responses include `branch_scores`
4. ✅ What-If returns `colleges_gained` and `colleges_lost`
5. ✅ Career roadmap has all 4 stages
6. ✅ Automated test suite shows 11/11 passed

---

## 📚 More Information

- **Full Documentation**: See `README_TESTING.md`
- **All Test Cases**: See `TEST_CASES.md`
- **Copy-Paste Commands**: See `COPY_PASTE_TESTS.md`
- **Interactive Testing**: Open `http://127.0.0.1:8080/docs`

---

## 🚀 Ready to Test!

**Start with the browser method** (easiest):

```
http://127.0.0.1:8080/docs
```

Then try the curl commands above!

**Happy Testing! 🎉**
