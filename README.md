# 🧭 Pathfinder — AI Career Counsellor

> AI-powered career counselling platform for Indian engineering students. Combines a **Groq-powered LLM** (Llama 3.3 70B) with a **deterministic rule engine** and a **custom NLP pipeline** to guide students to the right engineering branch and colleges based on psychometric signals, JEE/state rank, budget, and location preferences.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│   Frontend — React 19 + Vite 8 + TailwindCSS 4 + Zustand        │
│   (Chat UI, Confidence Meter, What-If Simulator, Compare Mode,   │
│    Option Entry List, PDF Export)                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │  REST API (JSON)
┌────────────────────────▼─────────────────────────────────────────┐
│   Backend — FastAPI (Async) + Pydantic v2                        │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │ 🤖 AI Engine (Groq)                                     │    │
│   │    Signal extraction · Counsellor responses · Summaries │    │
│   └─────────────────────────────────────────────────────────┘    │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │ 🧠 NLP Pipeline                                         │    │
│   │    Intent Classifier · Entity Extractor · TF-IDF Search │    │
│   └─────────────────────────────────────────────────────────┘    │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │ ⚙️  Rule Engine                                          │    │
│   │    Weighted signal→branch scoring · Tie detection       │    │
│   └─────────────────────────────────────────────────────────┘    │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │ 🎓 Recommendation Engine                                │    │
│   │    Rank-aware college tier classifier (Dream/Mod/Safe)  │    │
│   └─────────────────────────────────────────────────────────┘    │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │ 🔴 Reddit Layer                                         │    │
│   │    Real-world college insights via PRAW + Groq summary  │    │
│   └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Psychometric Signals** | Groq LLM extracts 8 aptitude signals (Logical Thinking, Creativity, Manual Work, Spatial Awareness, Biology Interest, Problem Solving, Communication, Math Aptitude) from conversational answers |
| 🧠 **NLP Pipeline** | Regex-based intent classifier, entity extractor (colleges, programs, tests, locations, financials), and TF-IDF cosine-similarity search over a seeded knowledge base |
| ⚙️ **Rule Engine** | Deterministic weighted scoring across 5 branches — CS, Electronics, Mechanical, Civil, Medical — with configurable signal-to-branch weight maps |
| 🔀 **Dynamic Questions** | Skips questions if the user already provided the info; injects AI-generated tie-breaker questions when top-2 branch scores are within 15% |
| 🎓 **College Classifier** | Classifies 700+ colleges into Dream / Moderate / Safe tiers against the student's JEE/State rank, filtered by budget and location |
| 📍 **Smart Location Backfill** | Strict location matching with automatic "Other Region" backfill if there are <5 colleges in your preferred state |
| 📝 **Manual Overrides** | AI detects when the user explicitly forces a branch change during confirmation, cleanly overwriting the exponential moving average |
| 📊 **Live Score Sidebar** | Real-time branch confidence meter updating as the chat progresses |
| 🎛️ **What-If Simulator** | Drag a rank slider to see how college tier options change dynamically |
| ⚖️ **Compare Mode** | Side-by-side comparison of any number of recommended colleges |
| 📋 **Option Entry List** | Priority-ordered choice list generated specifically for JOSAA/KCET counselling option entry |
| 📄 **PDF Export** | Export the full dynamic report as a high-quality PDF via html2canvas + jsPDF |
| 🔴 **Reddit Insights** | Real student reviews fetched (PRAW) and summarized (Groq) per college |

---

## 🔧 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.10+** | Runtime |
| **FastAPI** | Async REST API framework |
| **Pydantic v2** | Request/response validation and data models |
| **Groq SDK** | LLM inference (Llama 3.3 70B) |
| **PRAW** | Reddit API integration |
| **SlowAPI** | Rate limiting |
| **SQLAlchemy + aiosqlite** | Async database (optional persistence) |
| **Redis** | Session caching (optional, falls back to in-memory) |

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI framework |
| **Vite 8** | Build tool and dev server |
| **TailwindCSS 4** | Utility-first styling |
| **Zustand** | Lightweight global state management (persisted to localStorage) |
| **Axios** | HTTP client |
| **react-markdown** | Rendering markdown in chat responses |
| **jsPDF + html2canvas** | Client-side PDF generation |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerised deployment (backend, frontend, Redis) |
| **Nginx** | Frontend static file serving with SPA routing |

---

## 🔑 Required API Keys & Services

Create a `.env` file inside the `backend/` directory:

### ✅ Mandatory

| Variable | Where to get it | Purpose |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys | Powers all LLM calls (signal extraction, counsellor responses, summaries) |

> **Free tier** on Groq is generous — no credit card needed to start.

### ⚙️ Optional (but recommended for full features)

| Variable | Where to get it | Purpose |
|---|---|---|
| `REDDIT_CLIENT_ID` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Fetch real student reviews about colleges |
| `REDDIT_CLIENT_SECRET` | Same as above | Required alongside Client ID |
| `REDDIT_USER_AGENT` | Any string e.g. `Pathfinder/1.0 by u/yourusername` | Reddit API identifier |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) | Google search fallback for college insights |

> If Reddit keys are **not set**, the app still works fully — college Reddit insights will just be empty.

### Full `.env` template

```env
# ── Groq (REQUIRED) ─────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# ── Reddit API (optional — for college insights) ─────────────────────────────
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=Pathfinder/1.0 by u/yourredditusername

# ── Serper (optional — Google fallback) ──────────────────────────────────────
SERPER_API_KEY=your_serper_api_key

# ── Redis (optional — for caching; falls back to in-memory if not set) ───────
REDIS_URL=redis://localhost:6379/0

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./pathfinder.db

# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV=development
SECRET_KEY=change-this-to-a-random-secure-string-in-production
FRONTEND_URL=http://localhost:5173
BACKEND_PORT=8000
LOG_LEVEL=INFO

# ── Rate Limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=20
```

---

## 🚀 Running Locally (Without Docker)

### Prerequisites

- Python **3.10+**
- Node.js **18+** and npm
- Git

---

### Step 1 — Clone & set up environment variables

```bash
git clone <your-repo-url>
cd pathfinder
```

---

### Step 2 — Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env and fill in your GROQ_API_KEY at minimum
# (copy the template from the section above)

# Start the backend server
uvicorn main:app --reload --port 8000
```

Backend will be live at: **http://localhost:8000**
Interactive API docs: **http://localhost:8000/docs**

---

### Step 3 — Frontend

Open a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend will be live at: **http://localhost:5173**

---

## 🐳 Running via Docker (Recommended for production-like setup)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
# From the project root (pathfinder/)
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Redis | localhost:6379 |

To stop:
```bash
docker-compose down
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns version, uptime, active session count |
| `POST` | `/session/start` | Create a new counselling session, returns first question |
| `POST` | `/chat` | Send a user message, receive counsellor response + branch scores |
| `POST` | `/what-if` | Simulate recommendations for a hypothetical rank |
| `GET` | `/session/{id}` | Get current session state |
| `DELETE` | `/session/{id}` | Delete/restart a session |
| `GET` | `/branches` | List all available engineering branches in the dataset |

---

## 📁 Project Structure

```
pathfinder/
├── backend/
│   ├── main.py                          # FastAPI app — routes, middleware, session mgmt
│   ├── config.py                        # Centralised settings (Pydantic BaseSettings, reads .env)
│   ├── requirements.txt                 # Python dependencies
│   ├── .env                             # Environment variables (not committed)
│   │
│   ├── engines/
│   │   ├── rule_engine.py               # Weighted signal → branch scoring + tie detection
│   │   ├── recommendation.py            # College tier classifier (Dream / Moderate / Safe)
│   │   └── question_engine.py           # Dynamic question selection + category advancement
│   │
│   ├── services/
│   │   ├── ai_service.py                # Groq API integration + NLP pipeline orchestration
│   │   ├── reddit_service.py            # PRAW Reddit scraper (async via thread pool)
│   │   └── explanation.py               # Human-readable report & profile summary builder
│   │
│   ├── models/
│   │   ├── signals.py                   # SignalOutput schema (8 aptitude signals + metadata)
│   │   ├── user_profile.py              # UserProfile, BranchScores, Message, category order
│   │   └── college.py                   # College, CollegeRecommendation, tier types
│   │
│   ├── nlp/
│   │   ├── intent/classifier.py         # Regex-based intent classification (10 intents)
│   │   ├── entities/extractor.py        # Named entity extraction (colleges, programs, etc.)
│   │   ├── embeddings/search.py         # TF-IDF cosine similarity search engine
│   │   ├── context/manager.py           # Session-aware conversation context tracker
│   │   └── response/generator.py        # Fallback response generator
│   │
│   └── data/
│       ├── questions.json               # 14 curated psychometric questions across 7 categories
│       └── colleges.json                # 700+ college dataset with cutoffs, fees, placements
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile                       # Multi-stage: build → Nginx static serve
│   └── src/
│       ├── main.jsx                     # React entrypoint
│       ├── App.jsx                      # Main layout — landing, form, chat, results views
│       ├── App.css                      # Global styles (glassmorphism, gradients, glow)
│       ├── index.css                    # TailwindCSS imports
│       ├── components/
│       │   ├── ChatWindow.jsx           # Chat interface with auto-scroll & loading states
│       │   ├── InitialForm.jsx          # Pre-chat student info form
│       │   ├── ScoreSidebar.jsx         # Real-time branch score visualisation
│       │   ├── ConfidenceMeter.jsx      # Circular confidence indicator
│       │   ├── CollegeCard.jsx          # College recommendation card with compare toggle
│       │   └── WhatIfSlider.jsx         # Hypothetical rank slider simulator
│       ├── hooks/
│       │   ├── useSession.js            # Session lifecycle (start, send, clear)
│       │   └── useConversation.js       # Chat message management
│       └── store/
│           └── counsellorStore.js       # Zustand global state (persisted to localStorage)
│
├── JEE and NEET csv files/              # Raw counselling data (JOSAA, KCET, NEET rounds)
│   ├── 2021–2024 JOSAA round data (.xlsx)
│   ├── KCET 2024 mock allotments (.csv)
│   └── NEET 2021–2024 round allotments (.csv)
│
├── docker-compose.yml                   # 3-service stack: backend, frontend, Redis
├── explore_output.txt                   # Data exploration log for CSV parsing
└── .gitignore
```

---

## 🔬 How It Works

### 1. Psychometric Signal Extraction
The student chats naturally. After each message, the Groq LLM extracts 8 aptitude signals (0.0–1.0 each) via a strict JSON contract. The NLP pipeline enriches prompts with detected intent, extracted entities, and retrieved knowledge snippets.

### 2. Deterministic Branch Scoring
The **Rule Engine** applies a configurable weight matrix (`SIGNAL_BRANCH_MAP`) to map signals to branch scores. No AI makes the final branch call — this is fully deterministic and auditable.

### 3. Tie Detection & Breaking
If the gap between the top-2 branches is ≤ 15%, a dynamically generated tie-breaker question is injected (up to 2 rounds).

### 4. College Classification
Once the student confirms their profile, the **Recommendation Engine** classifies 700+ colleges into:
- **🌟 Dream** — cutoff is significantly better than student rank
- **🎯 Moderate** — within reasonable reach
- **🛡️ Safe** — student rank comfortably beats the cutoff

Colleges are filtered by branch, budget, and location, then sorted by placement average and fees.

### 5. Reddit Enrichment
For the top 6 colleges, real Reddit posts are fetched (PRAW) and summarized into 3 bullet points (Groq) covering sentiment, placements, and campus life.

---

## 🤖 Supported Groq Models

You can change `GROQ_MODEL` in your `.env`:

| Model | Speed | Best for |
|---|---|---|
| `llama-3.3-70b-versatile` *(default)* | Fast | Best quality, all tasks |
| `llama-3.1-8b-instant` | Ultra-fast | Lower latency, lighter usage |
| `mixtral-8x7b-32768` | Fast | Long context scenarios |
| `gemma2-9b-it` | Fast | Lightweight alternative |

Full list: [console.groq.com/docs/models](https://console.groq.com/docs/models)

---

## ✅ Running Tests

```bash
cd backend

# Activate your venv first (if not already)
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Mac/Linux

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_rule_engine.py -v
python -m pytest tests/test_question_engine.py -v
```

---

## 🛠️ Common Issues

| Problem | Solution |
|---|---|
| `GROQ_API_KEY not set` error | Make sure your `.env` file is inside the `backend/` directory |
| `ModuleNotFoundError: groq` | Run `pip install -r requirements.txt` inside your activated venv |
| Frontend can't reach backend (CORS error) | Ensure `FRONTEND_URL=http://localhost:5173` is set in `.env` and the backend is running on port 8000 |
| Reddit insights missing | Expected if `REDDIT_CLIENT_ID` is not set. The rest of the app works normally |
| Zustand state persists after restart | Clear `pathfinder-session` from localStorage in your browser |

---

## 📜 License

This project was built as a semester project (4th Semester — Engineering Experiential Learning).
