# Architecture Overview

## High‑Level System Diagram
The Pathfinder system consists of three major runtime components:
1. **Frontend (Vite‑React SPA)** – located in `frontend/`. Serves static assets (`index.html`, bundled JS/CSS) and communicates with the backend via a JSON REST API.
2. **Backend (FastAPI)** – located in `backend/`. Exposes the public API (`/start`, `/chat`, `/report`, etc.) and internal persistence routes (`/api/persistence/*`). It orchestrates two "engine" implementations:
   - `AdaptiveQuestionEngine` – deterministic rules‑based engine.
   - `LLMAdaptiveEngine` – LLM‑driven engine that calls the `services.llm_client` module.
   - Both engines share a common interface used by the FastAPI routes.
3. **MongoDB** – runs as a Docker container (defined in `docker-compose.yml`). Stores user sessions, chat history, resumes, roadmaps, assessments, and internship recommendations.

```
Client (Browser) --> Frontend (React) --> Backend (FastAPI) --> Engines (Python) --> MongoDB
```

### Execution Flow (Typical Session)
1. **Start Session** – `POST /start` creates a UUID session, initialises an engine state, and returns the first question.
2. **Chat Loop** – Frontend sends user answers to `POST /chat`. The backend sanitises input, forwards it to the selected engine, receives the next question and scoring data, persists the exchange via `middleware.persistence_middleware`.
3. **Report Generation** – When `engine.is_complete` the backend composes a final report (deterministic or LLM‑based) and may invoke the `recommend` function (from `engines.recommendation`) to fetch college recommendations.
4. **Persistence API** – Optional `/api/persistence/*` routes let a client retrieve stored user data (profile, chat history, resumes, etc.).

### Component Interaction Matrix
| Component | Depends On | Exposes |
|-----------|------------|---------|
| `frontend/src` | Backend HTTP API | UI, state management (React hooks) |
| `backend/main.py` | Engines, MongoDB, middleware | FastAPI app, public endpoints |
| `backend/engines/*` | `services.llm_client` (LLM engine) | Question generation, scoring |
| `backend/services/persistence_service.py` | `database.connection` | CRUD operations for MongoDB |
| `backend/database/connection.py` | `pymongo` (via `motor`) | Async connection lifecycle |
| `backend/middleware/persistence_middleware.py` | `services.persistence_service` | Automatic session start & chat logging |
| `backend/api/persistence_routes.py` | `services.persistence_service` | REST API for persisted data |

## Deployment Diagram
The `docker-compose.yml` defines two services:
- `frontend` – built from the `frontend/` Dockerfile, serves the React build on port 80.
- `backend` – built from the `backend/` context, runs `uvicorn` on port 8000.
- `mongodb` – official MongoDB image, persists data in a Docker volume.

```
┌───────────────┐   ┌─────────────┐   ┌───────────────┐
│   Browser     │←→│  Frontend   │←→│   Backend     │←→ MongoDB
│ (React SPA)   │   │ (nginx)    │   │ (FastAPI)    │
└───────────────┘   └─────────────┘   └───────────────┘
```

## Key Design Patterns
- **Dependency Injection** – Engines are instantiated once at app start and injected into request handlers.
- **Middleware** – `persistence_middleware` adds cross‑cutting concerns (session tracking, chat logging) without polluting endpoint logic.
- **Repository Pattern** – `services.persistence_service` abstracts MongoDB operations.
- **Factory** – Engine selection logic chooses deterministic vs. LLM based on request payload.

---
*All references point to actual source files (e.g., `backend/main.py`, `backend/engines/adaptive_engine.py`).*
