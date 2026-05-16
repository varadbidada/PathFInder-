# Backend Scripts

## build_college_db.py

Extracts real JoSAA cutoff data from Excel files and builds a clean college database.

### Usage

```bash
python backend/scripts/build_college_db.py
```

### Input

Reads JoSAA Round 6 (closing rank) Excel files from `JEE and NEET csv files/`:

- `2022Round6.xlsx`
- `2023Round6.xlsx`
- `2024Round5.xlsx` (2024 final round)

### Output

Generates `backend/data/colleges_josaa.json` with:

- **532 colleges** (168 IITs, 364 NITs/IIITs/GFTIs)
- **Real cutoff ranks** (3-year rolling average: 2022-2024)
- **Rank type** (`jee_advanced` for IITs, `jee_main` for NITs/IIITs)
- **11 branches**: CS, Electronics, Mechanical, Civil, Electrical, Chemical, Metallurgy, Mathematics and Computing, Engineering Physics, Aerospace, Biotechnology

### Key Features

1. **Multi-query extraction**: Reads all Round 6 files and averages cutoffs across 3 years
2. **Institute name canonicalization**: Maps verbose names like "Indian Institute of Technology Bombay" → "IIT Bombay"
3. **Branch normalization**: Maps program names like "Computer Science and Engineering (4 Years, Bachelor of Technology)" → "CS"
4. **Rank type separation**: IITs use JEE Advanced ranks, NITs/IIITs use JEE Main ranks (never compared directly)
5. **Validation**: Logs warnings for suspicious cutoff ranks (<50 or >500k)

### Sample Output

```
IIT Bombay CS: 65 (JEE Advanced)
IIT Delhi CS: 153 (JEE Advanced)
NIT Trichy CS: 2862 (JEE Main)
NIT Surathkal CS: 3310 (JEE Main)
```

### Validation

Run `test_recommendations.py` to verify:

- IIT Bombay CS cutoff is ~65 (not 100)
- NIT Trichy CS cutoff is ~2862 (not fabricated)
- JEE Advanced rank 2300 does NOT see IIT Bombay CS
- JEE Main rank 3000 DOES see NIT Trichy CS

```bash
python backend/scripts/test_recommendations.py
```

## test_recommendations.py

Tests the recommendation engine with real JoSAA data.

### Test Cases

1. **JEE Advanced rank 2300, CS**: Should NOT see IIT Bombay CS (cutoff ~65)
2. **JEE Main rank 3000, CS**: Should see NIT Trichy CS (cutoff ~2862)
3. **JEE Advanced rank 100, CS**: Should see IIT Bombay CS as Moderate/Safe

All tests should pass ✅

## Updating the Database

When new JoSAA data is released:

1. Download Round 6 Excel files for the new year
2. Place them in `JEE and NEET csv files/`
3. Update `ROUND6_FILES` in `build_college_db.py`
4. Run `python backend/scripts/build_college_db.py`
5. Run `python backend/scripts/test_recommendations.py` to validate

## Notes

- The recommendation engine automatically loads `colleges_josaa.json` if it exists, falling back to `colleges.json`
- Rank type filtering is CRITICAL: JEE Advanced and JEE Main ranks are never compared directly
- The 3-year rolling average smooths out anomalies in cutoff ranks
