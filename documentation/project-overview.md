# Project Overview

## Purpose
Pathfinder is an AI‑powered career counselling system that helps engineering students discover the engineering branch that best matches their interests, academic profile, and personal preferences. It interactively asks a series of adaptive questions, evaluates responses with either a deterministic rule‑based engine or a large‑language‑model (LLM) engine, and finally produces a personalised report with college recommendations.

## Core Features
- Adaptive interview flow (dynamic next‑question selection).
- Two engine modes: deterministic `AdaptiveQuestionEngine` and LLM‑driven `LLMAdaptiveEngine`.
- College recommendation integration (Dream/Moderate/Safe tiers).
- Persistence API for user profile, chat history, resumes, roadmaps, assessments, and internship suggestions.
- Docker‑Compose deployment of frontend, backend, and MongoDB.
- Extensible service layer for AI, Twitter/Reddit analysis, feedback, and more.

## High‑Level Architecture
```
Client (Browser) → Frontend (React/Vite) → Backend (FastAPI) → Engine (Python) → MongoDB
```
- Frontend lives in `frontend/` and communicates via JSON REST APIs.
- Backend (`backend/main.py`) hosts public endpoints and internal persistence routes.
- Engines (`backend/engines/`) encapsulate the core adaptive logic.
- Persistence uses async Motor driver to store data in MongoDB.

## Execution Flow (Typical Session)
1. **Start Session** – `POST /session/start` creates a UUID, selects engine based on LLM health, and returns opening question.
2. **Chat Loop** – `POST /chat` processes user answer, updates engine state, persists exchange, and returns next question.
3. **Completion** – Engine signals completion, backend composes final report and college recommendations.
4. **Data Retrieval** – Optional `GET /api/persistence/*` endpoints fetch stored user data.

## Key Files
- `backend/main.py` – FastAPI app and request handlers.
- `backend/engines/adaptive_engine.py` – Deterministic engine.
- `backend/engines/adaptive_engine_llm.py` – LLM engine wrapper.
- `backend/services/persistence_service.py` – MongoDB CRUD.
- `frontend/src/App.jsx` – React UI flow.
- `docker-compose.yml` – Service orchestration.

*All references include clickable `file://` links to the actual source files.*
