# Code Deep Dive

## Backend Entry Point – `backend/main.py`
- Sets up **FastAPI** app with CORS middleware.
- Uses an `asynccontextmanager` (`lifespan`) to manage MongoDB connection lifecycle.
- Defines the public API endpoints:
  - `GET /health` – health check with MongoDB status.
  - `GET /api/llm-status` – probes LLM provider health and decides which engine to use.
  - `POST /session/start` – creates a UUID session, selects engine (LLM if available), initialises engine state via `engine.create_session`, stores session metadata in the in‑memory `sessions` dict, and persists the start event with `persist_session_start`.
  - `POST /chat` – receives a user message, sanitises input, forwards it to the selected engine (`llm_engine` or `deterministic_engine`), logs the exchange via `persist_chat_exchange`, and when the engine signals completion composes a final report (`compose_final_report_*`).
- Session dict structure:
```json
{
  "session_id": {
    "created_at": "ISO timestamp",
    "engine_state": {...},
    "engine_type": "llm" | "deterministic",
    "raw_form": {...}
  }
}
```
- Uses **middleware** (`middleware/persistence_middleware.py`) to extract `user_id` from request headers and to automatically persist start/chat events.

## Adaptive Engines
### `backend/engines/adaptive_engine.py`
- Deterministic rule‑based engine.
- Implements `create_session`, `select_opening_question`, `process_answer`.
- Maintains a **Finite State Machine** (`conversation_fsm.py`) that tracks which question bucket to present next based on previous answers and confidence scores.
- Uses a **question bank** (`question_bank.py`) containing a curated list of engineering‑branch‑assessment questions.
- Scoring logic updates a `student_model` (see `models/student_model.py`) with trait scores and computes a confidence metric.

### `backend/engines/adaptive_engine_llm.py`
- Wrapper around an LLM (OpenAI/Groq) that drives the interview.
- `create_session` builds an initial system prompt describing the counsellor role and stores it in `engine_state`.
- `process_answer` sends the conversation history + user message to the LLM via `services/llm_client.py`, parses the JSON‑structured response (expected to contain `next_question`, `branch_hypothesis`, `confidence`, etc.).
- Provides a fallback to the deterministic engine when the LLM is unavailable.

## Persistence Service – `backend/services/persistence_service.py`
- Uses **Motor** (async MongoDB driver) to store:
  - Sessions (`sessions` collection)
  - Chat exchanges (`chat_history` collection)
  - User profile, resumes, roadmaps, assessments, internship recommendations.
- Each CRUD function returns simple Python structures (dicts/lists) that are forwarded to API responses.
- All persistence calls are awaited, keeping the request handling fully async.

## LLM Client – `backend/services/llm_client.py`
- Abstracts provider‑specific calls.
- Provides `check_llm_health()` – probes environment variables and attempts a lightweight request to verify API keys.
- `chat(messages: list[dict]) -> dict` – sends a list of messages to the selected provider (OpenAI or Groq) and returns the parsed JSON payload.
- Centralises error handling so the engine code stays clean.

## MongoDB Connection – `backend/database/connection.py`
- Exposes `connect_to_database`, `close_database_connection`, and `check_database_health`.
- Connection is stored in a module‑level variable `_client` for reuse across services.

## Frontend – `frontend/src/App.jsx`
- Root React component orchestrates the UI flow.
- Uses **Zustand** store (`store/useStore.js`) to keep session ID, current question, chat history, and UI state.
- Calls backend endpoints:
  - `POST /session/start` → receives `session_id` and first question.
  - `POST /chat` → submits user answer, receives next question, confidence, and optional report.
- Renders a chat‑like interface, shows progress bar, and finally displays a downloadable PDF report (via `jspdf`).
- Includes a **fallback UI** when the LLM is unavailable (shows a note and uses the deterministic engine).

## Key Data Models (`backend/models/`)
- `student_model.py` – Pydantic model representing trait scores, branch hypothesis, and confidence.
- `college.py` – Schema for college recommendation objects returned by `engines.recommendation.recommend`.
- `user_profile.py` – Stores static user information (name, email, exam type, rank, etc.).
- `signals.py` – Enumerates internal events used by the FSM (e.g., `ANSWER_RECEIVED`, `CONFIDENCE_UPDATED`).

## Important Helpers
- `backend/utils` (if present) – functions for sanitising input, normalising exam types, and selecting rank.
- `backend/middleware/persistence_middleware.py` – extracts `user_id` from request headers (or generates a temporary one) and injects it into persistence calls.

## How Components Interact
1. **Frontend** → HTTP request to **FastAPI**.
2. **FastAPI** routes retrieve the session, decide which **engine** to call.
3. **Engine** may call **LLM client** (network I/O) or run deterministic logic.
4. Engine updates **engine_state** and returns a response.
5. **Middleware** persists the exchange to **MongoDB** via **persistence_service**.
6. Final report may invoke the **recommendation** module to fetch college data.

---
*All file references use `file://` links for easy navigation.*
