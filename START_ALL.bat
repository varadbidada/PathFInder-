@echo off
echo ========================================
echo    Starting Pathfinder (Full Stack)
echo ========================================
echo.
echo Starting Backend Server...
start "Pathfinder Backend" cmd /k "cd backend && uvicorn main:app --reload --host 127.0.0.1 --port 8081"
echo Backend starting on: http://127.0.0.1:8081
echo.
timeout /t 3 /nobreak >nul
echo.
echo Starting Frontend Server...
start "Pathfinder Frontend" cmd /k "cd frontend && npm run dev"
echo Frontend starting on: http://localhost:5173
echo.
echo ========================================
echo    Both servers are starting!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8081
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8081/docs
echo.
echo Close the terminal windows to stop the servers
echo ========================================
pause
