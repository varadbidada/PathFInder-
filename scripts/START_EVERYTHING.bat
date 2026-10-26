@echo off
title Starting Pathfinder - AI Career Counsellor
echo.
echo ========================================
echo    🧭 Starting Pathfinder System
echo ========================================
echo.

echo 🤖 Checking Ollama...
"C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" list
echo.

echo 🔧 Starting Backend...
start "Backend" cmd /k "title Pathfinder Backend && cd backend && python main.py"
echo ⏳ Waiting 10 seconds for backend...
timeout /t 10 /nobreak >nul

echo 🎨 Starting Frontend...
start "Frontend" cmd /k "title Pathfinder Frontend && cd frontend && npm run dev"
echo ⏳ Waiting 5 seconds for frontend...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    🎉 PATHFINDER IS READY!
echo ========================================
echo.
echo 🌐 Open: http://localhost:5173
echo 🔧 Backend: http://127.0.0.1:8000
echo 📚 API Docs: http://127.0.0.1:8000/docs
echo.
echo 💡 Features Ready:
echo    ✅ Offline AI (Ollama + llama3.2:3b)
echo    ✅ Reactive conversations
echo    ✅ ML cutoff predictions
echo    ✅ Debug panel (🐛 button)
echo.

start http://localhost:5173
echo Opening Pathfinder...
echo.
echo Press any key to exit...
pause >nul