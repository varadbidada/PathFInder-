# 🎓 Pathfinder - AI Career Counsellor for Engineering Students

**Status**: ✅ **FULLY OPERATIONAL**

An AI-powered career counselling system that helps Indian engineering students choose the right branch and college based on their aptitude, interests, and JEE/NEET rank.

---

## 🚀 Quick Start

### 1. Start the Server

**Option A: Double-click** (Easiest)

```
START_SERVER.bat
```

**Option B: Command Line**

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

### 2. Running Pathfinder offline with Ollama

**Install Ollama:**

- **Windows**: Download from https://ollama.com
- **Mac/Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

**Pull a model (choose based on your RAM):**

- **8GB RAM**: `ollama pull llama3.2:3b`
- **16GB RAM**: `ollama pull mistral` ← recommended
- **32GB RAM**: `ollama pull llama3.1:70b`

**Verify Ollama is running:**

```bash
curl http://localhost:11434/api/tags
```

**Run Pathfinder without any API keys:**

```bash
cd backend
python main.py
```

**Check which provider is active:**

```bash
curl http://localhost:8000/api/llm-status
```

**To force Ollama even when GROQ_API_KEY is set:**

```bash
FORCE_OLLAMA=1 python main.py
```

### 3. Test the API

**Open in Browser** (Recommended)

```
http://127.0.0.1:8080/docs
```

This opens interactive API documentation where you can test all endpoints!

---

## 📊 Current Status

✅ **Server**: Running on `http://127.0.0.1:8080`  
✅ **Tests**: 11/11 passed (100%)  
✅ **Features**: All 9 tasks completed  
✅ **Documentation**: Complete

---

## ✨ Features

### Core Features (Tasks 1-8)

- ✅ Twitter/X sentiment analysis pipeline
- ✅ Real JoSAA cutoff data (2022-2024, 532 colleges)
- ✅ Enhanced Reddit insights with multi-post data
- ✅ Advanced sentiment analysis (VADER + TextBlob + Domain Lexicon)
- ✅ India-specific entity extraction (colleges, branches, exams, ranks)
- ✅ Multi-signal scoring (ability + enthusiasm)
- ✅ Context-aware conversation management
- ✅ Social media aggregation with Groq AI

### Novel Features (Task 9)

#### 🔮 Feature 9A: What-If Rank Simulator

Shows exactly what colleges you gain/lose by improving your rank.

- **Performance**: < 200ms ✓
- **Endpoint**: `POST /api/what-if`

#### 👥 Feature 9B: Peer Comparison

See what other students with similar ranks are choosing.

- **Database**: SQLite
- **Endpoints**: `GET /api/peer-stats`, `POST /api/peer-choice`

#### 📊 Feature 9C: Placement Reality Check

Distinguishes median salary (reality) from headline salary (marketing).

- **Feature**: Flags inflated stats (ratio > 3x)
- **Endpoint**: `POST /api/placement-reality`

#### 🗺️ Feature 9D: Branch-Career Roadmap

Realistic 5-year career roadmap for your chosen branch.

- **Stages**: 4 distinct stages (year_1, year_2_3, year_4, year_5) ✓
- **Endpoint**: `POST /api/career-roadmap`

#### 📄 Feature 9E: Parent Report

Comprehensive PDF-ready report for parents.

- **Content**: Branch, colleges, social proof, placement stats
- **Endpoint**: `POST /api/parent-report`

---

## 🧪 Testing

### Automated Tests

```bash
python test_pathfinder.py
```

**Result**: 11/11 tests passed ✅

### Manual Testing

See documentation files:

- **TRY_THESE_NOW.md** - Quick tests to run immediately
- **QUICK_START_GUIDE.md** - Comprehensive manual tests
- **TEST_CASES.md** - Detailed test cases
- **COPY_PASTE_TESTS.md** - Ready-to-use curl commands

---

## 📚 API Endpoints

### Session Management

- `POST /session/start` - Start counselling session
- `POST /chat` - Send message and get response
- `GET /session/{id}` - Get session state
- `DELETE /session/{id}` - Delete session

### Novel Features

- `POST /api/what-if` - What-If Rank Simulator
- `GET /api/peer-stats` - Peer comparison statistics
- `POST /api/peer-choice` - Store peer choice
- `POST /api/placement-reality` - Placement reality check
- `POST /api/career-roadmap` - Generate career roadmap
- `POST /api/parent-report` - Generate parent report

### Utility

- `GET /health` - Health check
- `GET /branches` - List available branches

**Full API Documentation**: `http://127.0.0.1:8080/docs`

---

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.111.0
- **Server**: Uvicorn 0.29.0
- **AI**: Groq API (llama-3.3-70b-versatile)
- **Database**: SQLite (peer comparison)
- **Sentiment**: VADER + TextBlob + Custom Domain Lexicon
- **NLP**: Custom entity extraction for Indian context
- **Rate Limiting**: SlowAPI
- **CORS**: Enabled for localhost

---

## 📁 Project Structure

```
Pathfinder/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Dependencies
│   ├── data/
│   │   ├── colleges_josaa.json # Real JoSAA data (532 colleges)
│   │   ├── colleges.json       # Additional colleges
│   │   └── questions.json      # Counselling questions
│   ├── engines/
│   │   ├── recommendation.py   # College recommendation engine
│   │   ├── rule_engine.py      # Branch scoring engine
│   │   └── question_engine.py  # Question selection logic
│   ├── models/
│   │   ├── user_profile.py     # User session model
│   │   ├── signals.py          # Signal extraction model
│   │   └── college.py          # College data model
│   ├── services/
│   │   ├── ai_service.py       # Groq AI integration
│   │   ├── novel_features.py   # Novel features (9A-9E)
│   │   ├── peer_comparison.py  # Peer comparison service
│   │   ├── reddit_service.py   # Reddit insights
│   │   ├── twitter_service.py  # Twitter analysis
│   │   └── explanation.py      # Report generation
│   ├── nlp/
│   │   ├── sentiment/          # Sentiment analysis
│   │   ├── entities/           # Entity extraction
│   │   ├── context/            # Context management
│   │   └── ...
│   └── scripts/
│       ├── verify_novel_features.py
│       └── test_*.py
├── frontend/                   # (Your frontend code)
├── test_pathfinder.py          # Automated test suite
├── START_SERVER.bat            # Server startup script
├── SERVER_INFO.txt             # Server information
├── README.md                   # This file
├── README_TESTING.md           # Test results summary
├── QUICK_START_GUIDE.md        # Manual test guide
├── TEST_CASES.md               # Comprehensive test cases
├── COPY_PASTE_TESTS.md         # Ready-to-use commands
└── TRY_THESE_NOW.md            # Quick tests
```

---

## 🎯 Example Usage

### 1. Start a Counselling Session

```bash
curl -X POST http://127.0.0.1:8080/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "jee_rank": 5000,
    "budget_lakh": 5,
    "preferred_location": "Bangalore"
  }'
```

### 2. Chat with the AI

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "user_message": "I love coding and solving problems"
  }'
```

### 3. Get What-If Analysis

```bash
curl -X POST http://127.0.0.1:8080/api/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "current_rank": 10000,
    "target_rank": 5000,
    "branch": "CS",
    "rank_type": "jee_main"
  }'
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Groq API (Required for AI features)
GROQ_API_KEY=your_groq_api_key_here

# Twitter API (Optional - for Twitter analysis)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Reddit API (Optional - for Reddit insights)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=Pathfinder/1.0

# Server Configuration
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
```

---

## 📈 Performance

| Endpoint               | Response Time | Status       |
| ---------------------- | ------------- | ------------ |
| /health                | < 10ms        | ✅           |
| /session/start         | < 100ms       | ✅           |
| /chat                  | < 500ms       | ✅           |
| /api/what-if           | 28ms          | ✅ (< 200ms) |
| /api/peer-stats        | < 50ms        | ✅           |
| /api/placement-reality | < 2s          | ✅           |
| /api/career-roadmap    | < 3s          | ✅           |
| /api/parent-report     | < 5s          | ✅           |

---

## 🐛 Troubleshooting

### Server not starting?

1. Check if port 8080 is available
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Check Python version: Python 3.8+

### Tests failing?

1. Make sure server is running: `curl http://127.0.0.1:8080/health`
2. Check dependencies are installed
3. Verify Groq API key is set (optional for basic tests)

### Port already in use?

Change port in `START_SERVER.bat`:

```batch
uvicorn main:app --reload --host 127.0.0.1 --port 8081
```

---

## 📝 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- **JoSAA Data**: Real cutoff data from JoSAA 2022-2024
- **Groq AI**: LLM inference
- **FastAPI**: Web framework
- **VADER**: Sentiment analysis

---

## 📞 Support

For issues or questions:

1. Check the test documentation files
2. Open `http://127.0.0.1:8080/docs` for interactive API testing
3. Run `python test_pathfinder.py` to verify all features

---

## 🎉 Status

**✅ ALL SYSTEMS OPERATIONAL**

- Server: Running
- Tests: 11/11 passed
- Features: All working
- Documentation: Complete

**Ready for use! 🚀**

---

**Last Updated**: May 13, 2026  
**Version**: 1.0.0  
**Test Status**: ✅ 100% PASSED
