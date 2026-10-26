# Pathfinder Class 12 Question System Redesign

## Overview

The entire question system has been redesigned from the ground up to work for Class 12 students who have **zero engineering or coding knowledge**. The new system replaces the fixed question bank with LLM-generated contextual questions based on a growing student personality model.

## Key Changes

### 1. Question Bank Redesign (`data/questions_class12.json`)

**Before:** Technical questions asking about DSA, circuits, coding knowledge
**After:** Class 12-friendly questions about personality, interests, and thinking style

The new question bank has:

- **3 fixed opener questions** that warm up the student
- **Stage templates** with example questions for LLM reference
- **Branch profiles** with ideal trait values for each engineering branch

No question requires technical knowledge. Every question can be answered by a 17-18 year old who just finished Class 12.

### 2. LLM Prompt System (`services/counsellor_prompts.py`)

All LLM prompts are now centralized in one file:

- **`SYSTEM_PROMPT`**: Defines the counsellor persona and rules
- **`build_extraction_prompt()`**: Extracts traits and generates next question
- **`build_confirmation_prompt()`**: Generates confirmation message at end
- **`build_retry_prompt()`**: Retries when LLM generates duplicate question
- **`get_branch_description()`**: Simple branch descriptions for students

**Key rules enforced:**

- ❌ NEVER ask about technical skills (coding, circuits, algorithms)
- ❌ NEVER use jargon (frontend, backend, DSA, IoT, PCB, API)
- ✅ ALWAYS ask ONE question per turn, naturally phrased
- ✅ ALWAYS react to what they just said

### 3. Student Model (`models/student_model.py`)

The `StudentModel` is a rich data structure that grows with each conversation turn:

```python
@dataclass
class StudentModel:
    # Numeric traits (0.0-1.0)
    math_aptitude: float = 0.5
    logical_thinking: float = 0.5
    creativity: float = 0.5
    hands_on: float = 0.5
    spatial_reasoning: float = 0.5
    biology_interest: float = 0.5
    problem_solving: float = 0.5

    # Categorical traits
    risk_appetite: str = None  # low/medium/high
    work_style: str = None     # solo/team/either
    memory_preference: str = None  # conceptual/rote/either

    # Qualitative profile (accumulated lists)
    interests: list = []
    aversions: list = []
    motivations: list = []
    contradictions: list = []
    notable_quotes: list = []

    # Hypothesis
    branch_hypothesis: str = "unknown"
    hypothesis_confidence: float = 0.0
```

**Updates use EMA (Exponential Moving Average):**

- New evidence is weighted 40% (α = 0.4)
- Old evidence is weighted 60%
- This prevents single answers from dominating

### 4. Adaptive Engine Redesign (`engines/adaptive_engine_llm.py`)

The LLM-powered engine now:

1. **Serves 3 fixed openers first** (turns 1-3)
2. **Calls LLM for contextual questions** (turns 4+)
3. **Extracts traits from student answers** using LLM
4. **Generates reactive next questions** based on what student just said
5. **Checks for duplicate questions** and retries if needed
6. **Advances through 5 stages**: personality → interest → thinking → aversion → confirmation
7. **Completes when confidence ≥ 0.75** or max questions reached

### 5. MongoDB Persistence

All session data is persisted to MongoDB, including:

```json
{
  "session_id": "...",
  "user_id": "...",
  "turn": 4,
  "question": "What the student was asked",
  "answer": "What the student said",
  "student_model_snapshot": {
    "math_aptitude": 0.72,
    "logical_thinking": 0.65,
    "interests": ["physics", "machines", "building things"],
    "branch_hypothesis": "Mech",
    "hypothesis_confidence": 0.68
  },
  "branch_scores": {"CS": 0.45, "ECE": 0.62, "Mech": 0.78, ...},
  "confidence": 0.68,
  "timestamp": "2025-01-..."
}
```

The new endpoint `/api/session/{session_id}/model` returns the current student model for debugging.

## Conversation Flow

### Stage 1: Personality (Fixed Openers, Turns 1-3)

These questions warm up the student and establish baseline personality:

1. **Saturday activity**: "If you had a completely free Saturday with no phone and no plans, what would you most likely end up doing?"
2. **Favorite subject**: "In school, which subject made you feel like time was flying when you were deep in it?"
3. **10-year vision**: "When you picture yourself 10 years from now — not what you think you should say, but what actually excites you — what are you doing?"

### Stage 2: Interest Probes (LLM-generated, 3-4 questions)

LLM generates questions based on what student said in Stage 1:

- If they mentioned physics → probe hands-on vs theory preference
- If they mentioned building things → ask about specific projects
- If they mentioned helping people → probe healthcare vs infrastructure

### Stage 3: Thinking Style (LLM-generated, 2-3 questions)

Questions about how they approach problems:

- Solo vs team preference
- Visual vs verbal thinking
- Structured vs open-ended tasks

### Stage 4: Aversion Check (LLM-generated, 2 questions)

What do they want to avoid?

- Work environments they'd hate
- Types of tasks that drain them

### Stage 5: Confirmation (1-2 questions)

LLM confirms the hypothesis:

"Based on what you've told me — especially your love for physics and taking things apart — I think Mechanical Engineering could be a great fit. Does that feel right to you?"

## Branch Mapping Logic

The system maps student traits to engineering branches using distance scoring:

### CS (Computer Science)

- **High**: logical_thinking (0.75), problem_solving (0.80), math_aptitude (0.70)
- **Low**: hands_on (0.30) — CS is less physical

### ECE (Electronics & Communication)

- **High**: logical_thinking (0.75), math_aptitude (0.75), hands_on (0.60)
- **Balanced**: Blend of software and hardware

### Mech (Mechanical)

- **High**: hands_on (0.80), spatial_reasoning (0.75), creativity (0.60)
- **Physical**: Building, machines, tangible systems

### Civil

- **High**: spatial_reasoning (0.80), creativity (0.70), hands_on (0.65)
- **Design-focused**: Structures, infrastructure

### Chemical

- **High**: biology_interest (0.70), logical_thinking (0.70), problem_solving (0.70)
- **Process-oriented**: Transformations, reactions

### Bio-tech

- **High**: biology_interest (0.85), logical_thinking (0.65)
- **Medical focus**: Health, diagnostics

## How LLM Generates Questions

Every time the student answers, the LLM:

1. **Extracts trait signals** from the answer (0.0-1.0 for numeric traits)
2. **Updates qualitative profile** (interests, aversions, motivations)
3. **Updates branch hypothesis** and confidence
4. **Generates next question** that:
   - Reacts to what student just said
   - Probes the most valuable unknown
   - Sounds natural and conversational
   - Contains zero jargon

**Example LLM output:**

```json
{
  "trait_updates": {
    "hands_on": 0.75,
    "spatial_reasoning": 0.68,
    "logical_thinking": 0.6
  },
  "profile_updates": {
    "interests": ["fixing bicycles", "radio electronics"],
    "motivations": ["helping people with technology"]
  },
  "branch_hypothesis": "Mech",
  "hypothesis_confidence": 0.68,
  "next_question": "When you fixed your bicycle, what part of the process did you enjoy most — figuring out what was wrong, or actually getting your hands dirty with the repair?",
  "next_question_reasoning": "Student mentioned fixing bicycle, probing whether they prefer diagnosis (logical) vs hands-on repair"
}
```

## Verification Test

Run the test script to validate the system:

```bash
cd backend
python test_class12_system.py
```

**Test scenario:** Student who should match Mechanical Engineering

**Test answers:**

1. "I'd probably spend it taking apart my old radio or fixing my bicycle."
2. "Physics was the best — especially when we derived things from scratch."
3. "I want to build machines that actually help people."

**Expected results:**

- ✅ Branch hypothesis: Mech or ECE
- ✅ Confidence > 0.4 after turn 6
- ✅ High hands_on score (> 0.6)
- ✅ Interests include physical/mechanical topics
- ✅ No duplicate questions

## API Changes

### New Response Fields

The `/chat` endpoint now returns additional fields when using LLM engine:

```json
{
  "session_id": "...",
  "assistant_message": "Next question text",
  "branch_scores": {"CS": 0.45, "Mech": 0.78, ...},
  "overall_confidence": 0.68,
  "trait_breakdown": {
    "math_aptitude": 0.65,
    "hands_on": 0.82,
    ...
  },
  "llm_reasoning": "Why LLM chose this question"
}
```

### New Endpoint

```
GET /api/session/{session_id}/model
```

Returns the current `StudentModel` for debugging:

```json
{
  "math_aptitude": 0.72,
  "logical_thinking": 0.65,
  "hands_on": 0.82,
  "interests": ["physics", "machines", "building"],
  "motivations": ["helping people"],
  "branch_hypothesis": "Mech",
  "hypothesis_confidence": 0.68
}
```

## Files Changed

### New Files

- `backend/data/questions_class12.json` — Class 12-friendly question bank
- `backend/services/counsellor_prompts.py` — All LLM prompts
- `backend/test_class12_system.py` — Verification test
- `CLASS12_REDESIGN_README.md` — This file

### Modified Files

- `backend/models/student_model.py` — Added EMA updates, branch scoring
- `backend/engines/adaptive_engine_llm.py` — Complete redesign for Class 12 students
- `backend/main.py` — Added student_model_snapshot support
- `backend/middleware/persistence_middleware.py` — Already supported snapshots

### Unchanged Files

- `backend/engines/adaptive_engine.py` — Deterministic engine (fallback)
- `backend/services/llm_client.py` — LLM client interface
- `backend/database/*` — MongoDB schemas

## Usage

### Start a Session

```bash
POST /session/start
{
  "exam_type": "jee_main",
  "jee_rank": 5000,
  "budget_lakh": 3,
  "preferred_location": "Karnataka"
}
```

### Chat

```bash
POST /chat
{
  "session_id": "...",
  "user_message": "I'd probably spend it fixing my bicycle"
}
```

### Check Student Model (Debug)

```bash
GET /api/session/{session_id}/model
```

## Configuration

The system automatically uses LLM if available, falls back to deterministic engine if not.

**To force Ollama (even if Groq key is set):**

```bash
export FORCE_OLLAMA=true
```

**To use Groq:**

```bash
export GROQ_API_KEY=your_key_here
```

**To check LLM status:**

```bash
GET /api/llm-status
```

## Future Enhancements

1. **Add more stage templates** for edge cases (student unsure, parent pressure, etc.)
2. **Multilingual support** (Hindi, Tamil, Telugu prompts)
3. **Video question delivery** (student sees counsellor avatar asking questions)
4. **Personality clustering** (group similar students for benchmarking)
5. **Interview prep mode** (practice answering college interview questions)

## Troubleshooting

### "No LLM available" error

**Solution:** Either set `GROQ_API_KEY` or install Ollama:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull mistral
```

### Questions repeating

**Solution:** The system checks for duplicates and retries. If this persists, check:

1. LLM temperature (should be 0.7-0.8)
2. Questions asked list is being maintained
3. Retry logic is working

### Branch hypothesis stuck at "unknown"

**Solution:** Student answers may be too vague. The LLM needs:

- Specific examples (not just "I like science")
- Action verbs (build, fix, design, analyze)
- Personal experiences (not just theory)

### Confidence not increasing

**Solution:** Check trait updates in student_model_snapshot:

- Are trait values being extracted? (should be 0.0-1.0)
- Are profile_updates being populated?
- Is EMA alpha too low? (try increasing from 0.4 to 0.5)

## Credits

Designed and implemented for Pathfinder AI Career Counsellor.
Focus: Making engineering branch selection accessible to Class 12 students.

---

**Last Updated:** January 2025
**Version:** 2.0.0
