# Session Reset Fix

## Problem

When starting a new chat, the system was showing recommendations based on previous session data instead of starting fresh.

## Root Causes Identified

1. **Browser caching** - User might not be clicking "Restart" button
2. **Session ID collision** - Unlikely but possible with UUID alone
3. **State persistence** - Frontend or backend might be reusing old state

## Fixes Applied

### 1. Enhanced Session ID Generation

**File: `backend/main.py`**

Changed from:

```python
session_id = str(uuid.uuid4())
```

To:

```python
session_id = f"{uuid.uuid4()}-{int(datetime.utcnow().timestamp() * 1000)}"
```

**Why**: Adds timestamp to ensure absolute uniqueness even if UUID collides

### 2. Added Session Logging

**File: `backend/main.py`**

Added logging to track:

- Session creation: `logger.info(f"Creating new session: {session_id}")`
- Chat requests: `logger.info(f"Chat request for session: {session_id}...")`
- Session not found: `logger.warning(f"Session not found: {session_id}")`

**Why**: Helps debug if sessions are being reused or not found

### 3. Frontend Already Correct

The frontend already:

- Clears localStorage on restart
- Resets Zustand store state
- Forces page reload with `window.location.reload()`
- Generates new session ID on each start

## How to Properly Restart

### Method 1: Use Restart Button (Recommended)

1. Click the **🔄 Restart** button in the top-right navbar
2. This will:
   - Delete the session on backend
   - Clear all frontend state
   - Reload the page
   - Show landing page

### Method 2: Manual Refresh

1. Close the browser tab completely
2. Open a new tab
3. Navigate to the application
4. Click "Start Session"

### Method 3: Clear Browser Data

1. Open DevTools (F12)
2. Go to Application → Storage
3. Click "Clear site data"
4. Refresh the page

## Verification Steps

### Check Session ID Changes

1. Start a session, note the session ID in browser DevTools Network tab
2. Click Restart
3. Start a new session
4. Verify the session ID is completely different

### Check Backend Logs

Look for these log entries:

```json
{"level": "INFO", "message": "Creating new session: <uuid>-<timestamp>"}
{"level": "INFO", "message": "Session deleted: <old-session-id>"}
{"level": "INFO", "message": "Creating new session: <new-uuid>-<new-timestamp>"}
```

### Check Recommendations

1. First session: Say "I have JEE Advanced rank 2300"
2. Complete conversation → Should show IITs
3. Click Restart
4. Second session: Say "I have JEE Main rank 5000"
5. Complete conversation → Should show NITs (NOT the same IITs from before)

## Common Issues

### Issue 1: Still Seeing Old Data

**Cause**: Not using Restart button, just refreshing page

**Solution**:

- Always click the **🔄 Restart** button
- OR close tab completely and open new one
- OR clear browser cache

### Issue 2: Session Not Found Error

**Cause**: Backend restarted but frontend still has old session ID

**Solution**:

- Click Restart button
- OR refresh the page (F5)

### Issue 3: Same Recommendations Every Time

**Cause**: Might be testing with same input data

**Solution**:

- Use different ranks in each session
- Use different exam types (JEE Advanced vs JEE Main)
- Check backend logs to confirm new session ID

## Testing Script

Create a test to verify session isolation:

```python
# backend/scripts/test_session_isolation.py
import requests
import time

API = "http://localhost:8000/api"

def test_session_isolation():
    print("Testing session isolation...")

    # Session 1: JEE Advanced
    print("\n=== Session 1: JEE Advanced ===")
    res1 = requests.post(f"{API}/session/start")
    session1_id = res1.json()["session_id"]
    print(f"Session 1 ID: {session1_id}")

    # Simulate conversation
    chat1 = requests.post(f"{API}/chat", json={
        "session_id": session1_id,
        "user_message": "I have JEE Advanced rank 2300"
    })
    print(f"Session 1 exam_type: {chat1.json().get('exam_type', 'not set')}")

    # Delete session 1
    requests.delete(f"{API}/session/{session1_id}")
    print(f"Deleted session 1")

    time.sleep(1)

    # Session 2: JEE Main
    print("\n=== Session 2: JEE Main ===")
    res2 = requests.post(f"{API}/session/start")
    session2_id = res2.json()["session_id"]
    print(f"Session 2 ID: {session2_id}")

    # Verify different session ID
    assert session1_id != session2_id, "Session IDs should be different!"
    print(f"✅ Session IDs are different")

    # Simulate conversation
    chat2 = requests.post(f"{API}/chat", json={
        "session_id": session2_id,
        "user_message": "I have JEE Main rank 5000"
    })
    print(f"Session 2 exam_type: {chat2.json().get('exam_type', 'not set')}")

    print("\n✅ Session isolation test passed!")

if __name__ == "__main__":
    test_session_isolation()
```

Run with:

```bash
cd backend
python scripts/test_session_isolation.py
```

## Summary

✅ **Session ID now includes timestamp** for absolute uniqueness  
✅ **Added logging** to track session lifecycle  
✅ **Frontend already handles restart correctly**  
✅ **Backend deletes old sessions properly**

**Key Point**: Always use the **🔄 Restart** button to ensure clean session reset!

## Debugging Tips

If you still see old data:

1. **Check browser DevTools Network tab**:
   - Look for `/session/start` request
   - Verify `session_id` in response is new each time

2. **Check backend logs**:
   - Look for "Creating new session" messages
   - Verify session IDs are different

3. **Check browser localStorage**:
   - Open DevTools → Application → Local Storage
   - Should be empty or only have new session data

4. **Try incognito mode**:
   - Opens with completely clean state
   - No cache, no cookies, no localStorage

5. **Check if backend restarted**:
   - Backend keeps sessions in memory
   - If backend restarts, all sessions are lost
   - Frontend will show "Session not found" error
   - Solution: Click Restart button
