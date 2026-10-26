# Pathfinder Class 12 System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  (React/Next.js - sends chat messages to backend)              │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/JSON
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│                     (main.py)                                   │
│                                                                 │
│  POST /session/start  ──►  Choose Engine (LLM or Deterministic)│
│  POST /chat           ──►  Process Answer → Get Next Question  │
│  GET /api/session/model ► Return StudentModel                  │
└────────────┬───────────────────────┬──────────────────────────┘
             │                       │
             ▼                       ▼
    ┌────────────────┐      ┌────────────────┐
    │  LLM Engine    │      │ Deterministic  │
    │ (adaptive_     │      │  Engine        │
    │  engine_llm.py)│      │ (fallback)     │
    └────────┬───────┘      └────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────────────┐
    │         CONVERSATION FLOW                        │
    │                                                  │
    │  Turn 1-3: Fixed Openers                        │
    │    │                                             │
    │    ├─ Q1: Saturday activity                     │
    │    ├─ Q2: Favorite subject                      │
    │    └─ Q3: 10-year vision                        │
    │                                                  │
    │  Turn 4+: LLM-Generated Questions               │
    │    │                                             │
    │    ├─ Stage 2: Interest Probes (3-4 Q)         │
    │    ├─ Stage 3: Thinking Style (2-3 Q)          │
    │    ├─ Stage 4: Aversion Check (2 Q)            │
    │    └─ Stage 5: Confirmation (1-2 Q)            │
    │                                                  │
    └───────────────┬──────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │   LLM CLIENT              │
        │  (llm_client.py)          │
        │                           │
        │  Priority:                │
        │  1. Groq (if API key)    │
        │  2. Ollama (if running)  │
        │  3. Error (no LLM)       │
        └──────────┬────────────────┘
                   │
                   ▼
       ┌────────────────────────────┐
       │  COUNSELLOR PROMPTS        │
       │  (counsellor_prompts.py)   │
       │                            │
       │  • SYSTEM_PROMPT           │
       │  • build_extraction_prompt │
       │  • build_confirmation      │
       │  • build_retry_prompt      │
       └──────────┬─────────────────┘
                  │
                  ▼
    ┌──────────────────────────────────────────┐
    │         LLM PROCESSING                   │
    │                                          │
    │  Input: Student Answer                  │
    │         Last Question                   │
    │         Current StudentModel            │
    │         Questions Asked So Far          │
    │                                          │
    │  Output: JSON {                         │
    │    trait_updates: {...}                 │
    │    profile_updates: {...}               │
    │    branch_hypothesis: "Mech"            │
    │    hypothesis_confidence: 0.68          │
    │    next_question: "..."                 │
    │  }                                       │
    └──────────┬───────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │   STUDENT MODEL              │
    │  (student_model.py)          │
    │                              │
    │  Numeric Traits (0-1):       │
    │  • math_aptitude             │
    │  • logical_thinking          │
    │  • creativity                │
    │  • hands_on                  │
    │  • spatial_reasoning         │
    │  • biology_interest          │
    │  • problem_solving           │
    │                              │
    │  Categorical:                │
    │  • risk_appetite             │
    │  • work_style                │
    │  • memory_preference         │
    │                              │
    │  Qualitative:                │
    │  • interests []              │
    │  • aversions []              │
    │  • motivations []            │
    │  • contradictions []         │
    │  • notable_quotes []         │
    │                              │
    │  Hypothesis:                 │
    │  • branch_hypothesis         │
    │  • hypothesis_confidence     │
    │                              │
    │  Methods:                    │
    │  • apply_updates() ──EMA──► │
    │  • calculate_branch_scores() │
    │  • get_top_branches()        │
    │  • to_dict()                 │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  BRANCH SCORING              │
    │                              │
    │  CS: {                       │
    │    logical_thinking: 0.75    │
    │    problem_solving: 0.80     │
    │    math_aptitude: 0.70       │
    │  }                           │
    │                              │
    │  ECE: {...}                  │
    │  Mech: {...}                 │
    │  Civil: {...}                │
    │  Chemical: {...}             │
    │  Bio-tech: {...}             │
    │                              │
    │  Score = 1 - avg_distance    │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │   PERSISTENCE                │
    │  (MongoDB)                   │
    │                              │
    │  Collections:                │
    │  • users                     │
    │  • chats (with snapshots)    │
    │  • resumes                   │
    │  • roadmaps                  │
    │  • assessments               │
    │                              │
    │  Each Chat Turn:             │
    │  {                           │
    │    question: "..."           │
    │    answer: "..."             │
    │    student_model_snapshot: { │
    │      traits: {...}           │
    │      interests: [...]        │
    │      hypothesis: "..."       │
    │      confidence: 0.68        │
    │    }                         │
    │    branch_scores: {...}      │
    │    timestamp: "..."          │
    │  }                           │
    └──────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────┐
│   User      │
│  (Class 12) │
└──────┬──────┘
       │
       │ "I love fixing bicycles"
       ▼
┌──────────────────────────────────────┐
│  POST /chat                          │
│  {                                   │
│    session_id: "...",                │
│    user_message: "I love fixing..." │
│  }                                   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  main.py → LLMAdaptiveEngine         │
│  process_answer()                    │
└──────┬───────────────────────────────┘
       │
       ├──► Get last question asked
       │
       ├──► Build extraction prompt
       │    (counsellor_prompts.py)
       │
       ▼
┌──────────────────────────────────────┐
│  LLM Client (Groq/Ollama)            │
│                                      │
│  Prompt includes:                    │
│  • Student answer                    │
│  • Last question                     │
│  • Current StudentModel              │
│  • Questions already asked           │
│  • Current stage                     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  LLM Returns JSON:                   │
│  {                                   │
│    "trait_updates": {                │
│      "hands_on": 0.75,               │
│      "spatial_reasoning": 0.68       │
│    },                                │
│    "profile_updates": {              │
│      "interests": ["fixing bicycles"]│
│    },                                │
│    "branch_hypothesis": "Mech",      │
│    "hypothesis_confidence": 0.65,    │
│    "next_question": "When you fixed │
│     your bicycle, what part did you │
│     enjoy most?"                     │
│  }                                   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  StudentModel.apply_updates()        │
│                                      │
│  Using EMA (α=0.4):                  │
│  new_value = old * 0.6 + new * 0.4  │
│                                      │
│  hands_on: 0.50 → 0.60 → 0.68 → ... │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Check for Duplicate Question        │
│                                      │
│  If similar to already asked:        │
│    → Retry with build_retry_prompt() │
│  Else:                               │
│    → Add to questions_asked[]        │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Calculate Branch Scores             │
│                                      │
│  For each branch:                    │
│    distance = Σ|student - ideal|     │
│    score = 1 - (distance / n_traits) │
│                                      │
│  Mech: 0.82 ★                        │
│  Civil: 0.75                         │
│  ECE: 0.68                           │
│  CS: 0.52                            │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Persist to MongoDB                  │
│                                      │
│  persist_chat_exchange()             │
│  • Question                          │
│  • Answer                            │
│  • student_model.to_dict()           │
│  • branch_scores                     │
│  • confidence                        │
│  • stage                             │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Return to Frontend                  │
│  {                                   │
│    "assistant_message": "Next Q",    │
│    "branch_scores": {...},           │
│    "overall_confidence": 0.65,       │
│    "trait_breakdown": {...},         │
│    "is_complete": false              │
│  }                                   │
└──────────────────────────────────────┘
```

## Stage Progression

```
┌────────────────────────────────────────────────────────────┐
│  STAGE 1: PERSONALITY (Turns 1-3)                         │
│  ────────────────────────────────────────                 │
│  Type: Fixed openers from questions_class12.json          │
│                                                            │
│  Q1: "If you had a free Saturday..."                      │
│  Q2: "Which subject made time fly..."                     │
│  Q3: "Picture yourself 10 years from now..."              │
│                                                            │
│  Extracts:                                                 │
│  • Baseline personality traits                            │
│  • Initial interests                                      │
│  • Rough motivations                                      │
└────────────────────────────────────────────────────────────┘
                             │
                             │ ready_for_next_stage: true
                             ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 2: INTEREST PROBES (Turns 4-6/7)                   │
│  ────────────────────────────────────────                 │
│  Type: LLM-generated, reactive to Stage 1 answers          │
│                                                            │
│  Examples:                                                 │
│  • "You mentioned physics — tell me more..."              │
│  • "When something breaks, what do you do?"               │
│  • "Hands-on experiment or reading theory?"               │
│                                                            │
│  Extracts:                                                 │
│  • Hands-on preference                                    │
│  • Curiosity style                                        │
│  • Domain interests (physics/biology/etc)                 │
└────────────────────────────────────────────────────────────┘
                             │
                             │ ready_for_next_stage: true
                             ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 3: THINKING STYLE (Turns 7-9)                      │
│  ────────────────────────────────────────                 │
│  Type: LLM-generated                                       │
│                                                            │
│  Examples:                                                 │
│  • "In a group project, what role do you take?"           │
│  • "Figure it out alone or ask someone?"                  │
│  • "Draw it out or just talk?"                            │
│                                                            │
│  Extracts:                                                 │
│  • work_style (solo/team/either)                          │
│  • Problem-solving approach                               │
│  • Visual vs verbal thinking                              │
└────────────────────────────────────────────────────────────┘
                             │
                             │ ready_for_next_stage: true
                             ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 4: AVERSION CHECK (Turns 9-10)                     │
│  ────────────────────────────────────────                 │
│  Type: LLM-generated                                       │
│                                                            │
│  Examples:                                                 │
│  • "Work environment you'd quit?"                         │
│  • "Part of school day you dread most?"                   │
│                                                            │
│  Extracts:                                                 │
│  • aversions []                                           │
│  • Negative signals (what to avoid)                       │
└────────────────────────────────────────────────────────────┘
                             │
                             │ confidence ≥ 0.75
                             ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 5: CONFIRMATION (Turns 10-11)                      │
│  ────────────────────────────────────────                 │
│  Type: LLM-generated from build_confirmation_prompt()      │
│                                                            │
│  Example:                                                  │
│  "Based on your love for physics and hands-on work,       │
│   I think Mechanical Engineering fits you well. Does      │
│   that feel right?"                                       │
│                                                            │
│  If student confirms: → Complete                          │
│  If student disagrees: → Ask follow-up                    │
└────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   COMPLETE     │
                    │                │
                    │  Return Report │
                    └────────────────┘
```

## Branch Scoring Algorithm

```python
def calculate_branch_scores(self) -> dict[str, float]:
    """
    Distance-based scoring: Lower distance = better fit
    """

    # Define ideal profiles
    branch_profiles = {
        "CS": {
            "logical_thinking": 0.75,
            "problem_solving": 0.80,
            "math_aptitude": 0.70,
            "creativity": 0.65,
            "hands_on": 0.30  # inverted: CS is less hands-on
        },
        "Mech": {
            "hands_on": 0.80,
            "spatial_reasoning": 0.75,
            ...
        },
        ...
    }

    scores = {}
    for branch, ideal_profile in branch_profiles.items():

        # Calculate distance for each trait
        total_distance = 0.0
        for trait, ideal_value in ideal_profile.items():
            student_value = getattr(self, trait, 0.5)
            distance = abs(student_value - ideal_value)
            total_distance += distance

        # Average distance
        avg_distance = total_distance / len(ideal_profile)

        # Convert to score (inverted)
        score = 1.0 - avg_distance
        scores[branch] = score

    return scores  # Higher = better fit
```

**Example:**

Student has:

- hands_on: 0.82
- spatial_reasoning: 0.71
- math_aptitude: 0.65

Mech ideal:

- hands_on: 0.80 → distance: 0.02
- spatial_reasoning: 0.75 → distance: 0.04
- math_aptitude: 0.65 → distance: 0.00

Avg distance: (0.02 + 0.04 + 0.00) / 3 = 0.02
Score: 1.0 - 0.02 = **0.98** ✨

## EMA Update Logic

```python
def apply_updates(self, trait_updates: dict, profile_updates: dict):
    """
    Exponential Moving Average (EMA) for smooth updates
    """

    alpha = 0.4  # Weight for new evidence

    for trait, new_value in trait_updates.items():
        if new_value is None:
            continue  # No new information

        current_value = getattr(self, trait)

        if current_value == 0.5:
            # First observation: use directly
            setattr(self, trait, new_value)
        else:
            # EMA: blend old and new
            updated = current_value * (1 - alpha) + new_value * alpha
            setattr(self, trait, updated)
```

**Example Evolution:**

```
Turn 1: hands_on = 0.50 (unknown)
        LLM extracts: 0.70
        → hands_on = 0.70 (first observation)

Turn 2: hands_on = 0.70
        LLM extracts: 0.85
        → hands_on = 0.70 * 0.6 + 0.85 * 0.4 = 0.76

Turn 3: hands_on = 0.76
        LLM extracts: 0.90
        → hands_on = 0.76 * 0.6 + 0.90 * 0.4 = 0.82

Converges to true value with less noise!
```

## Key Design Decisions

### 1. Why EMA instead of simple averaging?

**Problem:** Simple average gives equal weight to all observations.

- First vague answer: "I like science" → 0.55
- Strong confirmation later: "I love building robots" → 0.90
- Average: (0.55 + 0.90) / 2 = 0.72 ❌ Too low!

**Solution:** EMA weights recent evidence more:

- Turn 1: 0.55
- Turn 2: 0.55 _ 0.6 + 0.90 _ 0.4 = 0.69
- Turn 3: (more evidence) → converges to 0.82 ✅

### 2. Why fixed openers instead of LLM from turn 1?

**Problem:** LLM needs context to ask good questions.

**Solution:** 3 fixed openers establish baseline:

- Personality warmup
- Domain interests (PCM/PCB)
- Career motivations
- Then LLM has context for reactive questions

### 3. Why 5 stages instead of free-form conversation?

**Problem:** Free-form can miss important dimensions.

**Solution:** Structured stages ensure coverage:

- Personality → baseline
- Interest → domain preference
- Thinking → work style
- Aversion → elimination criteria
- Confirmation → validate hypothesis

### 4. Why distance-based scoring instead of rules?

**Problem:** Hard-coded rules are brittle.

- "IF hands_on > 0.7 AND physics > 0.6 THEN Mech" ❌

**Solution:** Distance to ideal profile is flexible:

- Each branch has ideal trait values
- Calculate how close student is to each
- Naturally handles partial fits

## File Structure

```
backend/
├── data/
│   └── questions_class12.json      ← Class 12-friendly questions
│
├── models/
│   └── student_model.py            ← StudentModel dataclass
│
├── services/
│   ├── llm_client.py               ← LLM interface (Groq/Ollama)
│   ├── counsellor_prompts.py       ← All LLM prompts ★NEW★
│   └── persistence_service.py      ← MongoDB operations
│
├── engines/
│   ├── adaptive_engine_llm.py      ← LLM-powered engine ★REDESIGNED★
│   └── adaptive_engine.py          ← Deterministic fallback
│
├── middleware/
│   └── persistence_middleware.py   ← Auto-persist to MongoDB
│
├── main.py                         ← FastAPI endpoints
│
├── quick_test.py                   ← Quick integration test ★NEW★
└── test_class12_system.py          ← Full verification test ★NEW★
```

## Summary

The redesigned system is:

✅ **Student-Friendly** — Zero technical knowledge required  
✅ **LLM-Powered** — Contextual, reactive questions  
✅ **Data-Rich** — Full StudentModel with 15+ dimensions  
✅ **Persistent** — Every turn saved to MongoDB  
✅ **Robust** — Duplicate detection, retry logic, fallbacks  
✅ **Testable** — Complete test coverage  
✅ **Documented** — Comprehensive docs + architecture

**Ready for production deployment! 🚀**
