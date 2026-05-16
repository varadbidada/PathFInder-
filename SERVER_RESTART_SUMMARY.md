# Server Restart Summary

## Date: May 14, 2026

---

## ✅ Server Restarted Successfully

### Actions Taken:

1. **Stopped all running processes**:
   - Python processes
   - Uvicorn processes
   - Node processes
   - Freed port 8080 and 5173

2. **Started fresh servers** using `START_ALL.bat`:
   - Backend server on `http://127.0.0.1:8080`
   - Frontend server on `http://localhost:5173`

### Current Status:

✅ **Backend**: Running on port 8080  
⏳ **Frontend**: Starting on port 5173 (npm takes 10-30 seconds)

---

## All Fixes Applied and Active

### 1. ✅ Exam Type Detection

- JEE Advanced → Only IITs
- JEE Main → Only NITs/IIITs
- Exam type extracted from user responses
- Properly passed to recommendation engine

### 2. ✅ Session Isolation

- Unique session IDs with timestamps
- Session collision detection
- Proper cleanup on restart
- Enhanced logging

### 3. ✅ Cumulative Signals

- Signals accumulate within session (weighted average)
- Signals reset between sessions
- 70% old + 30% new formula
- Consistent branch scoring

### 4. ✅ All Core Features Verified

- Centralized question bank (20+ questions)
- Duplicate detection (ID + 85% semantic similarity)
- Stage progression rules
- Tie-breaker limits (max 3)
- Backend session storage

---

## How to Test

### 1. Open the Application

```
http://localhost:5173
```

### 2. Test Exam Type Filtering

**Test A: JEE Advanced**

1. Click "Start Session"
2. Say: "I have JEE Advanced rank 2300"
3. Answer a few questions about your interests
4. Complete conversation
5. **Verify**: Only IITs in recommendations

**Test B: JEE Main (New Session)**

1. Click **🔄 Restart** button (important!)
2. Click "Start Session"
3. Say: "I have JEE Main rank 5000"
4. Answer questions (can be different from Test A)
5. Complete conversation
6. **Verify**: Only NITs/IIITs (NO IITs from previous session)

### 3. Test Cumulative Signals

**Within Same Session**:

1. Start session
2. Say: "I love coding" → Check CS score
3. Say: "I hate math" → CS score should adjust (not reset)
4. Say: "I enjoy problem solving" → CS score reflects all 3 messages
5. **Verify**: Scores accumulate, don't reset

### 4. Test Session Isolation

**Across Sessions**:

1. Session 1: Express interest in CS → Complete
2. Click **🔄 Restart**
3. Session 2: Express interest in Mechanical → Complete
4. **Verify**: No CS preference in Session 2

---

## Backend Logs to Monitor

Open the "Pathfinder Backend" command window and watch for:

### Good Logs (Expected):

```json
{"level": "INFO", "message": "Pathfinder API starting up"}
{"level": "INFO", "message": "Creating new session: <uuid>-<timestamp>"}
{"level": "INFO", "message": "Session created: <uuid> (Total active sessions: 1)"}
{"level": "INFO", "message": "Session <uuid>: Updated cumulative signals. Message #1"}
{"level": "INFO", "message": "Detected exam type: jee_advanced"}
{"level": "INFO", "message": "Session <uuid>: Branch scores - {'CS': 0.75, ...}"}
{"level": "INFO", "message": "Generating recommendations with rank_type=jee_advanced for rank=2300"}
```

### After Restart:

```json
{"level": "INFO", "message": "Session deleted: <old-uuid>"}
{"level": "INFO", "message": "Creating new session: <new-uuid>-<new-timestamp>"}
{"level": "INFO", "message": "Session created: <new-uuid> (Total active sessions: 1)"}
```

### Warning Logs (Indicates Issues):

```json
{"level": "WARNING", "message": "Session <uuid> already exists! This indicates improper restart."}
{"level": "WARNING", "message": "Session not found: <uuid>"}
{"level": "WARNING", "message": "Duplicate question detected (similarity: 87%)"}
```

---

## Command Windows

You should see two command windows:

### 1. Pathfinder Backend

- Shows backend logs
- Port: 8080
- Press Ctrl+C to stop

### 2. Pathfinder Frontend

- Shows Vite dev server
- Port: 5173
- Press Ctrl+C to stop

---

## Quick Verification Commands

### Check Server Status

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
Test-NetConnection -ComputerName 127.0.0.1 -Port 5173
```

### Test Backend API

```powershell
curl http://127.0.0.1:8080/docs
```

### View API Documentation

```
http://127.0.0.1:8080/docs
```

---

## If Servers Don't Start

### Backend Issues:

1. Check if port 8080 is in use: `netstat -ano | findstr :8080`
2. Check Python is installed: `python --version`
3. Check virtual environment: `.venv\Scripts\activate`
4. Check dependencies: `pip install -r requirements.txt`

### Frontend Issues:

1. Check if port 5173 is in use: `netstat -ano | findstr :5173`
2. Check Node is installed: `node --version`
3. Check dependencies: `npm install`
4. Manual start: `cd frontend && npm run dev`

---

## Manual Server Start (If Needed)

### Backend:

```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

### Frontend:

```bash
cd frontend
npm run dev
```

---

## Summary

✅ **All servers restarted with latest fixes**  
✅ **Backend running on port 8080**  
⏳ **Frontend starting on port 5173**  
✅ **All fixes active and ready to test**

**Next Step**: Open `http://localhost:5173` and test the application!

---

## Key Reminder

**Always use the 🔄 Restart button** when starting a new session to ensure:

- Old session is deleted
- New session ID is generated
- Cumulative signals are reset
- Clean slate for new user

**DO NOT** just refresh the page (F5) - this keeps the old session ID!
