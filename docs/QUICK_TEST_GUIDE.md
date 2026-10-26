# Quick Test Guide - Exam Type Fix

## Run Automated Tests

```bash
cd backend
python scripts/test_exam_type_fix.py
```

**Expected Output**:

```
✅ PASSED: No NITs found in JEE Advanced results
✅ PASSED: No IITs found in JEE Main results
✅ ALL TESTS PASSED
```

---

## Manual Testing

### Test Case 1: JEE Advanced User

1. Start backend: `python backend/main.py`
2. Open `frontend/index.html` in browser
3. Start conversation
4. When asked about rank, say: **"I have JEE Advanced rank 2300"**
5. Complete the conversation
6. **Verify**: Recommendations show ONLY IITs (IIT Ropar, IIT Gandhinagar, etc.)
7. **Verify**: NO NITs appear (NIT Trichy, NIT Surathkal, etc.)

### Test Case 2: JEE Main User

1. Start new conversation
2. When asked about rank, say: **"I got 5000 in JEE Main"**
3. Complete the conversation
4. **Verify**: Recommendations show ONLY NITs/IIITs (MNNIT, MNIT Jaipur, etc.)
5. **Verify**: NO IITs appear (IIT Bombay, IIT Delhi, etc.)

### Test Case 3: Ambiguous Input

1. Start new conversation
2. When asked about rank, say: **"My rank is 10000"** (no exam type mentioned)
3. Complete the conversation
4. **Expected**: System defaults to JEE Main (shows NITs/IIITs)

---

## Check Database

```bash
cd backend
python scripts/check_nit_rank_type.py
```

**Expected Output**:

```
NITs marked as jee_advanced: 0
IITs marked as jee_main: 0 (or only IIITs, not IITs)
Total colleges: 532
JEE Advanced: 168
JEE Main: 364
```

---

## Verify Logs

When running the application, check logs for:

```
INFO: Detected exam type: jee_advanced
INFO: Generating recommendations with rank_type=jee_advanced for rank=2300
```

---

## Common Issues

### Issue: Still seeing NITs for JEE Advanced

**Solution**:

1. Restart backend server
2. Clear browser cache
3. Start new conversation (don't reuse old session)

### Issue: Exam type not detected

**Solution**:

1. Explicitly mention "JEE Advanced" or "JEE Main" in your response
2. Check logs for "Detected exam type" message
3. If not detected, AI may need clearer input

### Issue: Groq API errors

**Solution**:

- This is expected (rate limiting)
- Reddit insights will be skipped
- Recommendations will still work
- No action needed

---

## Quick Validation Checklist

- [ ] Automated test passes
- [ ] JEE Advanced → Only IITs
- [ ] JEE Main → Only NITs/IIITs
- [ ] No NITs in JEE Advanced results
- [ ] No IITs in JEE Main results
- [ ] Database has 168 JEE Advanced colleges
- [ ] Database has 364 JEE Main colleges
- [ ] Logs show "Detected exam type" message
- [ ] Logs show "rank_type=jee_advanced" or "rank_type=jee_main"

---

## Success Criteria

✅ All automated tests pass  
✅ Manual testing confirms correct filtering  
✅ Database verification shows correct structure  
✅ Logs show exam type detection working  
✅ No NITs appear for JEE Advanced users  
✅ No IITs appear for JEE Main users

**If all criteria met**: Fix is working correctly! 🎉
