# 🎨 Frontend Setup Guide

## ✅ Configuration Updated

The frontend has been configured to connect to the backend at `http://127.0.0.1:8080`

---

## 🚀 Quick Start (Easiest Way)

### Option 1: Start Everything at Once

**Double-click this file:**

```
START_ALL.bat
```

This will open two terminal windows:

- **Backend** on `http://127.0.0.1:8080`
- **Frontend** on `http://localhost:5173`

Then open your browser to: `http://localhost:5173`

---

### Option 2: Start Separately

#### Step 1: Start Backend

**Double-click:**

```
START_SERVER.bat
```

Or run:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

#### Step 2: Start Frontend

**Double-click:**

```
START_FRONTEND.bat
```

Or run:

```bash
cd frontend
npm run dev
```

#### Step 3: Open Browser

```
http://localhost:5173
```

---

## 🔧 What Was Fixed

### 1. Backend URL Updated

**File**: `frontend/vite.config.js`

**Changed from:**

```javascript
target: 'http://localhost:8000',
```

**Changed to:**

```javascript
target: 'http://127.0.0.1:8080',
```

### 2. Dependencies Installed

Ran `npm install` in the frontend directory to install all required packages.

---

## 📊 Server URLs

| Service         | URL                          | Purpose                       |
| --------------- | ---------------------------- | ----------------------------- |
| **Frontend**    | `http://localhost:5173`      | Main application UI           |
| **Backend API** | `http://127.0.0.1:8080`      | REST API endpoints            |
| **API Docs**    | `http://127.0.0.1:8080/docs` | Interactive API documentation |

---

## 🧪 Testing the Connection

### Test 1: Check Backend is Running

Open in browser: `http://127.0.0.1:8080/health`

**Expected:**

```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### Test 2: Check Frontend is Running

Open in browser: `http://localhost:5173`

**Expected:** You should see the Pathfinder application UI

### Test 3: Test API Connection

1. Open frontend: `http://localhost:5173`
2. Fill in the initial form (rank, budget, location)
3. Click "Start Counselling"
4. If it works, the connection is successful! ✅

---

## 🔍 How the Connection Works

```
┌─────────────────┐
│   Browser       │
│  localhost:5173 │
└────────┬────────┘
         │
         │ HTTP Request to /api/*
         ↓
┌─────────────────┐
│  Vite Dev Server│
│  (Frontend)     │
│  Port 5173      │
└────────┬────────┘
         │
         │ Proxy: /api/* → http://127.0.0.1:8080/*
         ↓
┌─────────────────┐
│  FastAPI Server │
│  (Backend)      │
│  Port 8080      │
└─────────────────┘
```

**Example:**

- Frontend makes request to: `/api/session/start`
- Vite proxy forwards to: `http://127.0.0.1:8080/session/start`
- Backend processes and responds
- Frontend receives the response

---

## 🐛 Troubleshooting

### Frontend not loading?

**Check 1: Is the frontend server running?**

```bash
# You should see output like:
# VITE v8.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

**Check 2: Is the port 5173 available?**
If port 5173 is in use, Vite will automatically use the next available port (5174, 5175, etc.)

**Check 3: Check browser console**
Press F12 in browser → Console tab → Look for errors

---

### API calls failing?

**Check 1: Is backend running?**

```bash
curl http://127.0.0.1:8080/health
```

**Check 2: Check browser Network tab**
Press F12 → Network tab → Try an action → Look for failed requests

**Check 3: CORS errors?**
The backend is configured to allow requests from `http://localhost:5173`. If you see CORS errors, the backend might not be running.

---

### "Cannot connect to backend" error?

**Solution 1: Restart both servers**

1. Close both terminal windows
2. Double-click `START_ALL.bat`
3. Wait for both to start (about 5-10 seconds)
4. Refresh browser

**Solution 2: Check vite.config.js**
Make sure it says:

```javascript
target: 'http://127.0.0.1:8080',
```

**Solution 3: Clear browser cache**
Press Ctrl+Shift+Delete → Clear cache → Reload page

---

## 📁 Frontend Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── hooks/          # Custom hooks (API calls)
│   │   ├── useSession.js       # Session management
│   │   └── useConversation.js  # Chat functionality
│   ├── store/          # Zustand state management
│   ├── App.jsx         # Main app component
│   └── main.jsx        # Entry point
├── public/             # Static assets
├── vite.config.js      # Vite configuration (proxy setup)
└── package.json        # Dependencies
```

---

## 🎯 Key Frontend Features

The frontend includes:

- ✅ Initial form (rank, budget, location)
- ✅ Chat interface for counselling
- ✅ Branch recommendation display
- ✅ College recommendations (Dream/Moderate/Safe)
- ✅ What-If rank simulator
- ✅ Reddit/Twitter insights display
- ✅ PDF report generation

---

## 🔄 Development Workflow

### Making Changes

**Backend changes:**

1. Edit files in `backend/`
2. Server auto-reloads (uvicorn --reload)
3. Refresh browser to see changes

**Frontend changes:**

1. Edit files in `frontend/src/`
2. Vite auto-reloads (Hot Module Replacement)
3. Browser updates automatically

---

## 📝 Environment Variables

If you need to configure API keys:

**Backend** (`.env` in `backend/` directory):

```env
GROQ_API_KEY=your_groq_api_key
TWITTER_BEARER_TOKEN=your_twitter_token
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

**Frontend** (`.env` in `frontend/` directory):

```env
# Not needed - uses proxy configuration
```

---

## 🎉 Success Checklist

- ✅ Backend running on `http://127.0.0.1:8080`
- ✅ Frontend running on `http://localhost:5173`
- ✅ Can access frontend in browser
- ✅ Can start counselling session
- ✅ Chat messages work
- ✅ Recommendations display

---

## 🚀 Next Steps

1. **Double-click `START_ALL.bat`** to start both servers
2. **Open browser** to `http://localhost:5173`
3. **Test the application**:
   - Fill in rank, budget, location
   - Start counselling
   - Answer questions
   - See recommendations

---

## 📞 Quick Reference

**Start Everything:**

```
Double-click: START_ALL.bat
```

**Frontend URL:**

```
http://localhost:5173
```

**Backend API:**

```
http://127.0.0.1:8080
```

**API Documentation:**

```
http://127.0.0.1:8080/docs
```

---

**Ready to use! 🎉**

Just double-click `START_ALL.bat` and open `http://localhost:5173` in your browser!
