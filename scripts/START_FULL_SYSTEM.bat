@echo off
echo ========================================
echo    🚀 Starting Pathfinder Full System
echo ========================================

echo.
echo 📊 Checking system status...

REM Check if backend is running
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend not running. Starting backend...
    echo.
    echo 🔧 Starting Backend Server...
    start "Pathfinder Backend" cmd /k "cd backend && python main.py"
    echo ⏳ Waiting for backend to start...
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Backend already running
)

echo.
echo 🎨 Starting Frontend Server...
start "Pathfinder Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ⏳ Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

echo.
echo 🧪 Testing system connection...
python test_frontend_backend_connection.py

echo.
echo ========================================
echo    🎉 System Status Check Complete
echo ========================================
echo.
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend:  http://127.0.0.1:8000
echo 📚 API Docs: http://127.0.0.1:8000/docs
echo.
echo Press any key to continue...
pause >nul