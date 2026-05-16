@echo off
title Pathfinder - AI Career Counsellor
color 0A

echo.
echo ========================================
echo    🧭 PATHFINDER - AI Career Counsellor
echo ========================================
echo.

REM Check if Ollama is installed
echo 🤖 Checking Ollama status...
"C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" list >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama not found or not working
    echo Please install Ollama from https://ollama.com
    pause
    exit /b 1
)

REM Check if models are available
"C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" list | findstr "llama3.2:3b" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing AI model (llama3.2:3b)...
    echo This may take a few minutes...
    "C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" pull llama3.2:3b
    if %errorlevel% neq 0 (
        echo ❌ Failed to install model
        pause
        exit /b 1
    )
)

echo ✅ Ollama and model ready

REM Check if backend is running
echo.
echo 🔧 Checking backend status...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo 🚀 Starting backend server...
    start "Pathfinder Backend" cmd /k "title Pathfinder Backend && cd backend && echo Starting Pathfinder Backend... && echo. && python main.py"
    
    echo ⏳ Waiting for backend to start (30 seconds)...
    timeout /t 30 /nobreak >nul
    
    REM Verify backend started
    curl -s http://127.0.0.1:8000/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Backend failed to start
        echo Please check the backend window for errors
        pause
        exit /b 1
    )
) else (
    echo ✅ Backend already running
)

REM Check if frontend is running
echo.
echo 🎨 Checking frontend status...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% neq 0 (
    echo 🚀 Starting frontend server...
    start "Pathfinder Frontend" cmd /k "title Pathfinder Frontend && cd frontend && echo Starting Pathfinder Frontend... && echo. && npm run dev"
    
    echo ⏳ Waiting for frontend to start (15 seconds)...
    timeout /t 15 /nobreak >nul
) else (
    echo ✅ Frontend already running
)

echo.
echo 🧪 Testing system integration...
python test_chat_flow.py

echo.
echo ========================================
echo    🎉 PATHFINDER IS READY!
echo ========================================
echo.
echo 🌐 Frontend:    http://localhost:5173
echo 🔧 Backend:     http://127.0.0.1:8000
echo 📚 API Docs:    http://127.0.0.1:8000/docs
echo 🤖 LLM Status:  http://127.0.0.1:8000/api/llm-status
echo.
echo 💡 Features:
echo    ✅ Offline AI with Ollama (llama3.2:3b)
echo    ✅ Reactive counsellor conversations
echo    ✅ ML-powered cutoff predictions
echo    ✅ Real-time branch scoring
echo.
echo 🚀 Opening Pathfinder in your browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Press any key to close this window...
pause >nul