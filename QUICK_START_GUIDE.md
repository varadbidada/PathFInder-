# 🚀 Pathfinder - Quick Start Guide

## ✅ Server Status

**Server is RUNNING** on: `http://127.0.0.1:8080`

**API Documentation**: `http://127.0.0.1:8080/docs` (Swagger UI - Interactive)

---

## 📊 Test Results Summary

**All 11 automated tests PASSED! (100%)**

✅ Health Check  
✅ List Branches  
✅ Start Session  
✅ Chat Flow  
✅ Get Session  
✅ **Feature 9A** - What-If Simulator (28ms < 200ms ✓)  
✅ **Feature 9B** - Peer Comparison  
✅ **Feature 9C** - Placement Reality Check  
✅ **Feature 9D** - Career Roadmap (4 stages ✓)  
✅ **Feature 9E** - Parent Report  
✅ Error Handling

---

## 🎯 Quick Manual Test Cases

### 1. Test Health Check (Browser)

Open in browser: `http://127.0.0.1:8080/health`

**Expected**:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-13T...",
  "version": "1.0.0",
  "active_sessions": 0
}
```

---

### 2. Interactive API Documentation (Browser)

Open in browser: `http://127.0.0.1:8080/docs`

- Click on any endpoint to expand
- Click "Try it out"
- Fill in parameters
- Click "Execute"
- See response below

**Recommended endpoints to try**:

1. `POST /session/start` - Start a counselling session
2. `POST /chat` - Have a conversation
3. `POST /api/what-if` - Test the What-If simulator
4. `POST /api/career-roadmap` - Get a career roadmap

---

### 3. Complete Counselling Flow (Postman/cURL)

#### Step 1: Start Session

```bash
curl -X POST http://127.0.0.1:8080/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "jee_rank": 5000,
    "budget_lakh": 5,
    "preferred_location": "Bangalore"
  }'
```

**Save the `session_id` from response!**

#### Step 2: Answer Questions

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID_HERE",
    "user_message": "I love coding and solving problems. Math is my favorite subject and I spend hours programming for fun."
  }'
```

**Repeat 3-4 times with different answers**:

- "I enjoy building things with my hands"
- "I'm interested in biology and medicine"
- "I like designing and creative work"

#### Step 3: Check Session State

```bash
curl http://127.0.0.1:8080/session/YOUR_SESSION_ID_HERE
```

#### Step 4: Confirm and Get Recommendations

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID_HERE",
    "user_message": "yes, proceed"
  }'
```

**Expected**: Full report with Dream/Moderate/Safe colleges!

---

### 4. Test Novel Features

#### Feature 9A: What-If Rank Simulator

**Question**: "What if I improve my rank from 10000 to 5000?"

```bash
curl -X POST http://127.0.0.1:8080/api/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "current_rank": 10000,
    "target_rank": 5000,
    "branch": "CS",
    "rank_type": "jee_main"
  }'
```

**Expected**: List of colleges gained/lost

---

#### Feature 9B: Peer Comparison

**Question**: "What are other students with my rank choosing?"

```bash
curl "http://127.0.0.1:8080/api/peer-stats?branch=CS&rank=5000"
```

**Expected**: Peer statistics and message

---

#### Feature 9C: Placement Reality Check

**Question**: "What are the real placement stats for IIT Bombay CS?"

```bash
curl -X POST http://127.0.0.1:8080/api/placement-reality \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Bombay",
    "branch": "Computer Science"
  }'
```

**Expected**: Median vs headline salary, inflation ratio

---

#### Feature 9D: Career Roadmap

**Question**: "What's the 5-year career path for CS?"

```bash
curl -X POST http://127.0.0.1:8080/api/career-roadmap \
  -H "Content-Type: application/json" \
  -d '{
    "branch": "Computer Science",
    "college_tier": "Moderate"
  }'
```

**Expected**: 4 stages (year_1, year_2_3, year_4, year_5)

---

#### Feature 9E: Parent Report

**Question**: "Generate a report for parents"

```bash
curl -X POST http://127.0.0.1:8080/api/parent-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID_HERE",
    "student_name": "Rahul Kumar"
  }'
```

**Expected**: Comprehensive report with branch, colleges, social proof

---

## 🧪 Test Scenarios

### Scenario 1: CS-Oriented Student

**Profile**: Loves coding, math, problem-solving  
**Expected Branch**: Computer Science  
**Test Messages**:

1. "I love coding and spend hours on LeetCode"
2. "Math is my favorite subject, especially algorithms"
3. "I enjoy solving logical puzzles"

---

### Scenario 2: Mechanical-Oriented Student

**Profile**: Hands-on, likes building things  
**Expected Branch**: Mechanical Engineering  
**Test Messages**:

1. "I enjoy working with my hands and building things"
2. "I like understanding how machines work"
3. "I prefer practical work over theory"

---

### Scenario 3: Medical-Oriented Student

**Profile**: Interested in biology, helping people  
**Expected Branch**: Medical/Biotechnology  
**Test Messages**:

1. "I'm fascinated by biology and the human body"
2. "I want to help people and make a difference in healthcare"
3. "I enjoy learning about diseases and treatments"

---

### Scenario 4: Civil Engineering Student

**Profile**: Creative, likes design, spatial thinking  
**Expected Branch**: Civil Engineering  
**Test Messages**:

1. "I enjoy designing and creating structures"
2. "I'm good at visualizing 3D objects"
3. "I like working on large-scale projects"

---

## 🔍 Edge Cases to Test

### 1. Rank Extraction

Test if the system extracts rank from natural language:

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "user_message": "My JEE Main rank is 12000"
  }'
```

**Expected**: Rank extracted and stored

---

### 2. Budget Extraction

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "user_message": "My budget is 5 lakh per year"
  }'
```

**Expected**: Budget extracted and stored

---

### 3. Invalid Session ID

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "invalid_id_12345",
    "user_message": "Hello"
  }'
```

**Expected**: 404 error with message

---

### 4. Empty Message

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "user_message": ""
  }'
```

**Expected**: 400 error - "Message cannot be empty"

---

### 5. Out of Range Rank

```bash
curl -X POST http://127.0.0.1:8080/api/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "current_rank": 2000000,
    "target_rank": 5000,
    "branch": "CS"
  }'
```

**Expected**: 422 Validation Error

---

## 📝 Python Test Script

Run the automated test suite:

```bash
cd "c:\Users\theva\OneDrive\Documents\4th sem\Pathfinder"
python test_pathfinder.py
```

**Expected**: All 11 tests pass (100%)

---

## 🎨 Frontend Integration

If you have a frontend, update the API base URL to:

```javascript
const API_BASE_URL = "http://127.0.0.1:8080";
```

**CORS is enabled** for:

- `http://localhost:5173` (Vite)
- `http://localhost:3000` (React)
- Frontend URL from config

---

## 🐛 Troubleshooting

### Server not responding?

Check if it's running:

```bash
curl http://127.0.0.1:8080/health
```

### Port already in use?

Change port in startup command:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8081
```

### Dependencies missing?

```bash
cd backend
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **Full Test Cases**: See `TEST_CASES.md`
- **API Documentation**: `http://127.0.0.1:8080/docs`
- **Redoc Documentation**: `http://127.0.0.1:8080/redoc`

---

## ✨ Key Features Implemented

✅ **Task 1-8**: Twitter/Reddit analysis, JoSAA data, sentiment analysis, entity extraction, context management  
✅ **Task 9A**: What-If Rank Simulator (< 200ms)  
✅ **Task 9B**: Peer Comparison with SQLite  
✅ **Task 9C**: Placement Reality Check (median vs headline)  
✅ **Task 9D**: Career Roadmap (4 stages)  
✅ **Task 9E**: Parent Report Generator

---

## 🎉 Ready to Use!

The Pathfinder API is fully functional and tested. All novel features are working as expected!

**Happy Testing! 🚀**
