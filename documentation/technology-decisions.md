# Technology Decisions

## Backend
- **FastAPI** – Provides async HTTP handling, automatic OpenAPI docs, and easy dependency injection. Chosen for its performance and Pythonic design. Alternatives: Flask (more lightweight but less async support), Django (heavier, includes ORM). Replacing FastAPI would require re‑writing async routes and losing built‑in docs.
- **Python 3.11+** – Modern language features, type hints, and async/await. Alternatives: Node.js (different ecosystem), Go (compiled, but requires rewriting all logic).
- **Pydantic** – Data validation and settings management. Alternative: marshmallow, dataclasses. Would affect request/response schemas.
- **Motor (async MongoDB driver)** – Non‑blocking DB access. Alternative: PyMongo (sync) or an SQL database with SQLAlchemy. Changing would impact async flow and persistence design.
- **OpenAI / Groq** – LLM providers used via `services/llm_client.py`. Alternatives: Anthropic, Azure OpenAI. Swapping providers mainly changes API keys and client wrapper.
- **Docker Compose** – Container orchestration for dev/prod. Alternatives: Kubernetes (more complex) or plain VMs.

## Frontend
- **React 19 + Vite** – Fast development server, modern JSX/TSX support. Alternatives: Vue, Angular, Svelte. Changing would require a full rewrite of UI components.
- **Tailwind CSS** – Utility‑first styling, easy theming. Alternatives: CSS modules, Styled‑components. Would affect styling approach.
- **Zustand** – Simple state management. Alternatives: Redux, Jotai, Context API. Would change how global UI state is handled.
- **Axios** – HTTP client for API calls. Alternatives: fetch API, superagent. Minimal impact.

## Other Services
- **Redis (optional)** – Caching layer (present in `requirements.txt`). Could be used for rate‑limiting or session caching. Alternatives: Memcached.
- **Twitter / Reddit analysis** – Implemented via `tweepy`, `praw`, and sentiment libraries. Alternatives: custom scrapers or third‑party APIs.
- **Data extraction** – `openpyxl`, `pandas` for JoSAA data. Alternatives: CSV parsers.

## Build & Deployment
- **Docker** – Containerization of both frontend and backend. Guarantees environment parity.
- **Vite** – Frontend bundler, enables hot‑module replacement.

## Why These Fit
- As an AI‑driven, async‑heavy service, FastAPI + Motor provide non‑blocking I/O.
- React + Vite give rapid UI iteration and easy integration with REST APIs.
- Using LLM providers via a thin client allows swapping models without core code changes.

## Interview Talking Points
- Emphasize async design, separation of concerns (engine vs. service), and how Docker Compose simplifies deployment.
- Discuss trade‑offs between deterministic vs. LLM engine.
- Mention scalability considerations (horizontal scaling of FastAPI workers, MongoDB sharding).
