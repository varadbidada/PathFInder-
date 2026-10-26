# 🚀 How to Start Pathfinder

## ⚡ Quick Start (Recommended)

### Step 1: Start Everything

**Double-click this file:**

```
START_ALL.bat
```

This will open two terminal windows:

- ✅ Backend server (API)
- ✅ Frontend server (UI)

### Step 2: Open Browser

```
http://localhost:5173
```

**That's it! You're ready to use Pathfinder! 🎉**

---

## 🌐 URLs

| Service           | URL                          | What it does                      |
| ----------------- | ---------------------------- | --------------------------------- |
| **Frontend (UI)** | `http://localhost:5173`      | Main application - **OPEN THIS!** |
| **Backend (API)** | `http://127.0.0.1:8080`      | REST API endpoints                |
| **API Docs**      | `http://127.0.0.1:8080/docs` | Interactive API testing           |

---

## 🎯 What You'll See

### Frontend (http://localhost:5173)

- 📝 Initial form to enter rank, budget, location
- 💬 Chat interface for counselling
- 🎓 Branch recommendations
- 🏫 College recommendations (Dream/Moderate/Safe)
- 🔮 What-If rank simulator
- 📊 Social media insights
- 📄 PDF report generation

### Backend API Docs (http://127.0.0.1:8080/docs)

- 📚 Interactive API documentation
- 🧪 Test endpoints directly
- 📖 See request/response formats

---

## 🔧 Alternative: Start Separately

### Option 1: Backend Only

```
Double-click: START_SERVER.bat
```

Or:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

### Option 2: Frontend Only

```
Double-click: START_FRONTEND.bat
```

Or:

```bash
cd frontend
npm run dev
```

---

## ✅ Verify Everything is Working

### Check 1: Backend Health

Open in browser: `http://127.0.0.1:8080/health`

**Should see:**

```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### Check 2: Frontend Loading

Open in browser: `http://localhost:5173`

**Should see:** Pathfinder application with initial form

### Check 3: Test Connection

1. Fill in the form (rank, budget, location)
2. Click "Start Counselling"
3. If it works → ✅ Everything is connected!

---

## 🐛 Troubleshooting

### Problem: "Cannot connect to backend"

**Solution:**

1. Make sure backend is running: `http://127.0.0.1:8080/health`
2. If not, double-click `START_SERVER.bat`
3. Wait 5 seconds, then refresh frontend

---

### Problem: Frontend not loading

**Solution:**

1. Check if frontend server is running (look for terminal window)
2. If not, double-click `START_FRONTEND.bat`
3. Check the URL - should be `http://localhost:5173`

---

### Problem: Port already in use

**Backend (port 8080):**
Edit `START_SERVER.bat` and change:

```
--port 8080  →  --port 8081
```

Then update `frontend/vite.config.js`:

```javascript
target: 'http://127.0.0.1:8081',
```

**Frontend (port 5173):**
Vite will automatically use next available port (5174, 5175, etc.)

---

## 🎓 How to Use Pathfinder

### Step 1: Initial Form

- Enter your JEE/NEET rank
- Enter your budget (in lakhs per year)
- Enter preferred location (optional)
- Click "Start Counselling"

### Step 2: Answer Questions

- The AI will ask you questions about your interests
- Answer naturally - the AI understands conversational language
- Examples:
  - "I love coding and solving problems"
  - "I enjoy working with my hands"
  - "I'm interested in biology and medicine"

### Step 3: Get Recommendations

- After 5-7 questions, you'll get:
  - Recommended branch (CS, Mechanical, Civil, etc.)
  - Confidence score
  - College recommendations (Dream/Moderate/Safe tiers)
  - Social media insights
  - Placement statistics

### Step 4: Explore Features

- **What-If Simulator**: See what colleges you can get with better rank
- **Peer Comparison**: See what others with your rank chose
- **Career Roadmap**: Get 5-year career plan
- **Parent Report**: Generate PDF report

---

## 📊 Test Data

Want to test quickly? Use these sample profiles:

### Profile 1: CS Enthusiast

- Rank: 3000
- Budget: 10 lakhs
- Message: "I love coding and spend hours on programming"

### Profile 2: Mechanical Engineer

- Rank: 15000
- Budget: 5 lakhs
- Message: "I enjoy working with machines and building things"

### Profile 3: Medical Student

- Rank: 5000 (NEET)
- Budget: 8 lakhs
- Message: "I'm passionate about biology and helping people"

---

## 📁 Important Files

| File                 | Purpose                         |
| -------------------- | ------------------------------- |
| `START_ALL.bat`      | Start both backend and frontend |
| `START_SERVER.bat`   | Start backend only              |
| `START_FRONTEND.bat` | Start frontend only             |
| `FRONTEND_SETUP.md`  | Detailed frontend setup guide   |
| `SERVER_INFO.txt`    | Backend server information      |
| `README_TESTING.md`  | Test results and documentation  |

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Two terminal windows are open (backend + frontend)
2. ✅ `http://localhost:5173` shows the application
3. ✅ You can fill the form and start counselling
4. ✅ Chat messages get responses
5. ✅ Recommendations appear after answering questions

---

## 🚀 Ready to Start!

**Just double-click `START_ALL.bat` and open `http://localhost:5173`!**

**Happy Counselling! 🎓**
