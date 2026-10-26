# JoSAA Cutoff Data Integration — Complete

## Summary

Replaced fabricated cutoff ranks in `colleges.json` with **real JoSAA 2022-2024 data** extracted from official Excel files.

## What Changed

### 1. New Script: `backend/scripts/build_college_db.py`

Extracts real cutoff data from JoSAA Round 6 Excel files:

- Reads `2022Round6.xlsx`, `2023Round6.xlsx`, `2024Round5.xlsx`
- Filters for **OPEN category, Gender-Neutral** seats only
- Computes **3-year rolling average** to smooth anomalies
- Maps institute names: `"Indian Institute of Technology Bombay"` → `"IIT Bombay"`
- Maps program names: `"Computer Science and Engineering (4 Years, Bachelor of Technology)"` → `"CS"`
- Assigns `rank_type`: `"jee_advanced"` for IITs, `"jee_main"` for NITs/IIITs/GFTIs
- Validates cutoffs: warns if rank < 50 or > 500k

**Output**: `backend/data/colleges_josaa.json` (532 colleges, 11 branches)

### 2. Updated: `backend/models/college.py`

Added `rank_type` field to `College` model:

```python
rank_type: str = "jee_main"  # "jee_advanced" or "jee_main"
```

### 3. Updated: `backend/engines/recommendation.py`

- Loads `colleges_josaa.json` by default (falls back to `colleges.json`)
- Added `rank_type` parameter to `recommend()` function
- **CRITICAL**: Filters colleges by `rank_type` to prevent comparing JEE Advanced ranks with JEE Main cutoffs
- Added `validate_cutoffs()` function to log warnings for suspicious data

### 4. Test Script: `backend/scripts/test_recommendations.py`

Validates the updated recommendation engine:

- ✅ JEE Advanced rank 2300 does NOT see IIT Bombay CS (cutoff ~65)
- ✅ JEE Main rank 3000 DOES see NIT Trichy CS (cutoff ~2862)
- ✅ JEE Advanced rank 100 sees IIT Bombay CS as Moderate/Safe

## Key Results

### Before (Fabricated Data)

- IIT Bombay CS: **100** ❌
- IIT Delhi CS: **120** ❌
- NIT Trichy CS: **Not in database** ❌

### After (Real JoSAA Data)

- IIT Bombay CS: **65** ✅ (JEE Advanced)
- IIT Delhi CS: **153** ✅ (JEE Advanced)
- IIT Madras CS: **224** ✅ (JEE Advanced)
- NIT Trichy CS: **2862** ✅ (JEE Main)
- NIT Surathkal CS: **3310** ✅ (JEE Main)
- NIT Warangal CS: **2559** ✅ (JEE Main)

## Database Stats

- **Total colleges**: 532
- **IITs (JEE Advanced)**: 168
- **NITs/IIITs/GFTIs (JEE Main)**: 364
- **Branches**: CS (111), Electronics (88), Mechanical (74), Civil (70), Electrical (54), Chemical (43), Metallurgy (32), Mathematics and Computing (26), Engineering Physics (19), Aerospace (8), Biotechnology (7)
- **Cutoff range**: 65 – 207,515

## Acceptance Criteria — All Met ✅

1. ✅ IIT Bombay CS cutoff is **65** (between 50-100)
2. ✅ NIT Trichy CS cutoff is **2862** (between 1000-4000)
3. ✅ Student with JEE Advanced rank 2300 does NOT see IIT Bombay CS
4. ✅ Script runs without errors: `python backend/scripts/build_college_db.py`

## Usage

### Generate Database

```bash
python backend/scripts/build_college_db.py
```

### Test Recommendations

```bash
python backend/scripts/test_recommendations.py
```

### API Usage (Updated)

```python
from engines.recommendation import recommend

# JEE Advanced student
recs = recommend(
    student_rank=2300,
    branch="CS",
    rank_type="jee_advanced",  # NEW: specify rank type
    budget_lakh=2.0,
    preferred_location="Maharashtra"
)

# JEE Main student
recs = recommend(
    student_rank=3000,
    branch="CS",
    rank_type="jee_main",  # NEW: specify rank type
    budget_lakh=2.0,
    preferred_location="Tamil Nadu"
)
```

## Files Modified

1. `backend/scripts/build_college_db.py` — NEW
2. `backend/scripts/test_recommendations.py` — NEW
3. `backend/scripts/README.md` — NEW
4. `backend/data/colleges_josaa.json` — NEW (532 colleges)
5. `backend/models/college.py` — Added `rank_type` field
6. `backend/engines/recommendation.py` — Added rank type filtering + validation
7. `backend/requirements.txt` — Added `openpyxl`, `pandas`

## Next Steps

1. Update frontend to ask user: "Which exam did you take? JEE Advanced / JEE Main"
2. Pass `rank_type` to the recommendation API
3. Update `main.py` to accept `rank_type` in `/chat` endpoint
4. Add user profile field: `exam_type: Literal["jee_advanced", "jee_main"]`

## Notes

- The recommendation engine automatically uses `colleges_josaa.json` if it exists
- Rank type filtering is **mandatory** — JEE Advanced and JEE Main ranks are never compared
- The 3-year rolling average (2022-2024) provides stable, realistic cutoffs
- All 532 colleges have been validated for suspicious ranks
