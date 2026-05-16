# Testing Guide - New Scoring System

## Server Status

The backend server should be starting. Check the command windows that opened:

- **"Pathfinder Backend"** - Backend server on port 8080
- **"Pathfinder Frontend"** - Frontend server on port 5173

If you don't see these windows, run `START_ALL.bat` manually.

---

## How to Test the New Scoring System

### Test 1: Within-Session Aggregation

**Goal**: Verify that signals accumulate within a single session

**Steps**:

1. Open `http://localhost:5173`
2. Click "Start Session"
3. **Message 1**: Say "I love coding and programming"
   - Watch the branch scores update
   - Note the CS score
4. **Message 2**: Say "I hate mathematics"
   - CS score should adjust (not reset!)
   - Should be average of both messages
5. **Message 3**: Say "I enjoy solving problems"
   - CS score should reflect all 3 messages
   - Should be average of all responses

**Expected Result**:

- ✅ Scores change with each message
- ✅ Scores reflect average of ALL messages in session
- ✅ Scores don't reset to zero after each message

---

### Test 2: Cross-Session Isolation (MOST IMPORTANT!)

**Goal**: Verify that new sessions have NO memory of previous sessions

**Steps**:

#### Session 1:

1. Open `http://localhost:5173`
2. Click "Start Session"
3. Say: **"I have JEE Advanced rank 2300"**
4. Say: **"I love computer science and coding"**
5. Answer a few more questions expressing CS interest
6. Complete the conversation
7. **Note the recommendations**: Should show IITs with CS focus

#### Session 2 (After Restart):

1. **IMPORTANT**: Click the **🔄 Restart** button (top-right)
2. Wait for page to reload
3. Click "Start Session" again
4. Say: **"I have JEE Main rank 5000"**
5. Say: **"I love mechanical work and building things"**
6. Answer questions expressing Mechanical interest
7. Complete the conversation
8. **Check recommendations**: Should show NITs with Mechanical focus

**Expected Result**:

- ✅ Session 2 shows Mechanical recommendations
- ✅ NO CS recommendations from Session 1
- ✅ NO IITs from Session 1 (should show NITs for JEE Main)
- ✅ Completely different branch scores

**If you see CS or IITs in Session 2**: The system is NOT working correctly!

---

### Test 3: Empty Session Handling

**Goal**: Verify that a new session starts with no scores

**Steps**:

1. Click **🔄 Restart**
2. Click "Start Session"
3. **Before answering any questions**, check the branch scores in the sidebar
4. All scores should be 0% or very low

**Expected Result**:

- ✅ All branch scores start at 0% or near 0%
- ✅ No branch is pre-selected
- ✅ No recommendations yet

---

## What to Look For

### ✅ Good Signs (System Working):

1. **Within Session**:
   - Scores update after each message
   - Scores reflect average of all messages
   - Scores are consistent and predictable

2. **Across Sessions**:
   - New session has different session ID
   - New session starts with 0% scores
   - New session has NO memory of previous session
   - Recommendations match current session only

3. **Backend Logs**:
   ```json
   {"message": "Session <uuid>: Aggregated signals from 3 messages"}
   {"message": "Session <uuid>: Branch scores - {'CS': 0.75, ...}"}
   {"message": "Session deleted: <old-uuid>"}
   {"message": "Creating new session: <new-uuid>"}
   ```

### ❌ Bad Signs (System NOT Working):

1. **Within Session**:
   - Scores reset to 0 after each message
   - Scores don't change at all
   - Scores are random or inconsistent

2. **Across Sessions**:
   - New session shows scores from previous session
   - New session shows same recommendations
   - Session ID doesn't change after restart
   - CS recommendations appear in Mechanical session

3. **Backend Logs**:
   ```json
   {"level": "WARNING", "message": "Session already exists!"}
   {"level": "ERROR", "message": "..."}
   ```

---

## Debugging Steps

### If Scores Don't Update:

1. Check backend logs for errors
2. Verify backend is running on port 8080
3. Check browser console for errors
4. Try refreshing the page

### If Sessions Aren't Isolated:

1. **MUST click 🔄 Restart button** (not just refresh!)
2. Check backend logs for "Session deleted" message
3. Verify new session ID is different
4. Clear browser cache if needed
5. Try incognito mode

### If Backend Won't Start:

1. Check if port 8080 is in use: `netstat -ano | findstr :8080`
2. Kill any process using port 8080
3. Check for Python errors in the command window
4. Try running manually: `cd backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080`

---

## Backend Logs to Monitor

Open the "Pathfinder Backend" command window and watch for:

### Session Creation:

```json
{"level": "INFO", "message": "Creating new session: abc123-1715654400000"}
{"level": "INFO", "message": "Session created: abc123-1715654400000 (Total active sessions: 1)"}
```

### Signal Aggregation:

```json
{"level": "INFO", "message": "Session abc123: Aggregated signals from 1 messages"}
{"level": "INFO", "message": "Session abc123: Aggregated signals from 2 messages"}
{"level": "INFO", "message": "Session abc123: Aggregated signals from 3 messages"}
```

### Branch Scoring:

```json
{
  "level": "INFO",
  "message": "Session abc123: Branch scores - {'CS': 0.75, 'Mechanical': 0.45, ...}"
}
```

### Session Deletion:

```json
{ "level": "INFO", "message": "Session deleted: abc123-1715654400000" }
```

### New Session (After Restart):

```json
{"level": "INFO", "message": "Creating new session: def456-1715654500000"}
{"level": "INFO", "message": "Session created: def456-1715654500000 (Total active sessions: 1)"}
```

**Key Point**: Session IDs should be DIFFERENT after restart!

---

## Quick Verification Commands

### Check if Backend is Running:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
```

### Check if Frontend is Running:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 5173
```

### Test Backend API:

```powershell
curl http://127.0.0.1:8080/docs
```

### View API Documentation:

Open in browser: `http://127.0.0.1:8080/docs`

---

## Summary

### What Changed:

- ❌ Removed cumulative signals (weighted average)
- ✅ Added simple average of current session only
- ✅ Each session is completely independent

### How to Test:

1. ✅ Test within-session aggregation (scores update)
2. ✅ Test cross-session isolation (no memory)
3. ✅ Test empty session (starts at 0%)

### Key Points:

- **Always click 🔄 Restart** to start a new session
- **Check backend logs** to verify session IDs change
- **Verify recommendations** match current session only

### Success Criteria:

- ✅ Scores aggregate within session
- ✅ New sessions have NO memory
- ✅ Recommendations match current session
- ✅ Different session IDs after restart

---

## If Everything Works:

You should see:

1. ✅ Session 1: CS recommendations for CS interest
2. ✅ Click Restart
3. ✅ Session 2: Mechanical recommendations for Mechanical interest
4. ✅ NO CS recommendations in Session 2!

**This proves the new system is working correctly!** 🎉
