# How to Restart a New Chat Session Properly

## The Right Way ✅

### Step 1: Click the Restart Button

Look for the **🔄 Restart** button in the top-right corner of the navbar.

### Step 2: Wait for Page Reload

The page will automatically reload and show the landing page.

### Step 3: Click "Start Session"

Click the **✨ Start Session** button to begin a fresh conversation.

### Step 4: Verify Clean Start

- You should see the welcome message
- No previous conversation history
- Branch scores should be at 0%
- No previous recommendations

---

## What Happens When You Click Restart

1. **Backend**: Deletes your old session data
2. **Frontend**: Clears all stored state
3. **Browser**: Reloads the page completely
4. **Result**: Brand new session with clean slate

---

## Common Mistakes ❌

### ❌ Mistake 1: Just Refreshing the Page (F5)

**Problem**: Keeps the old session ID, backend might still have old data

**Solution**: Use the Restart button instead

### ❌ Mistake 2: Clicking "Start Session" Without Restart

**Problem**: Might create a new session but browser could cache old data

**Solution**: Always click Restart first

### ❌ Mistake 3: Using Browser Back Button

**Problem**: Goes back to old session state

**Solution**: Use the Restart button

---

## Alternative Methods

### Method 1: Close Tab Completely

1. Close the browser tab (not just minimize)
2. Open a new tab
3. Navigate to Pathfinder
4. Click "Start Session"

**When to use**: If Restart button isn't working

### Method 2: Incognito/Private Mode

1. Open a new incognito/private window
2. Navigate to Pathfinder
3. Click "Start Session"

**When to use**: For testing or if you suspect caching issues

### Method 3: Clear Browser Data

1. Open DevTools (F12)
2. Go to Application → Storage
3. Click "Clear site data"
4. Refresh the page

**When to use**: If nothing else works

---

## How to Verify You Have a Clean Session

### Check 1: Session ID

1. Open DevTools (F12)
2. Go to Network tab
3. Look for `/session/start` request
4. Check the `session_id` in the response
5. It should be a long UUID with timestamp

### Check 2: Conversation History

- Messages panel should be empty
- No previous questions visible
- No previous answers visible

### Check 3: Branch Scores

- All branches should show 0% or very low scores
- No branch should be highlighted as recommended yet

### Check 4: Recommendations

- No college recommendations should be visible
- Results panel should be empty

---

## Testing Different Scenarios

### Scenario 1: Test JEE Advanced, Then JEE Main

**Session 1**:

1. Start session
2. Say: "I have JEE Advanced rank 2300"
3. Complete conversation
4. **Verify**: Only IITs in recommendations

**Session 2** (after restart):

1. Click Restart
2. Start new session
3. Say: "I have JEE Main rank 5000"
4. Complete conversation
5. **Verify**: Only NITs/IIITs in recommendations (NO IITs from previous session)

### Scenario 2: Test Different Branches

**Session 1**:

1. Start session
2. Express interest in CS
3. Complete conversation
4. **Verify**: CS recommendations

**Session 2** (after restart):

1. Click Restart
2. Start new session
3. Express interest in Mechanical
4. Complete conversation
5. **Verify**: Mechanical recommendations (NO CS from previous session)

---

## Troubleshooting

### Problem: Still Seeing Old Recommendations

**Possible Causes**:

1. Didn't click Restart button
2. Backend still running old session
3. Browser caching aggressively

**Solutions**:

1. Click Restart button (not just refresh)
2. Check backend logs for "Creating new session" message
3. Try incognito mode
4. Clear browser cache completely

### Problem: "Session Not Found" Error

**Cause**: Backend restarted but frontend has old session ID

**Solution**:

1. Click Restart button
2. OR refresh the page (F5)
3. Start a new session

### Problem: Same Session ID Every Time

**Cause**: Backend not generating new IDs properly

**Solution**:

1. Check backend logs
2. Restart backend server
3. Verify backend code has timestamp in session ID generation

---

## For Developers: Verify Backend

### Check Backend Logs

Look for these patterns:

```json
{"level": "INFO", "message": "Creating new session: <uuid>-<timestamp>"}
{"level": "INFO", "message": "Session deleted: <old-id>"}
{"level": "INFO", "message": "Creating new session: <new-uuid>-<new-timestamp>"}
```

### Run Automated Test

```bash
cd backend
python scripts/test_session_isolation.py
```

Expected output:

```
✅ Session 1 created
✅ Session 1 deleted
✅ Session 2 created
✅ Session IDs are different
✅ SESSION ISOLATION TEST PASSED
```

---

## Summary

✅ **Always use the 🔄 Restart button**  
✅ **Wait for page to reload completely**  
✅ **Verify session ID changes in DevTools**  
✅ **Check that old data doesn't appear**

**Remember**: The Restart button is your friend! It ensures a completely clean slate for each new conversation.
