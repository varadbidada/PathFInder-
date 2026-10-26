@echo off
echo ========================================
echo    Starting Pathfinder Servers
echo ========================================
echo.

REM Check if backend is already running
echo Checking if port 8080 is available...
netstat -ano | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8080 is already in use!
    echo Please close any existing backend server first.
    pause
    exit /b 1
)

REM Check if frontend is already running
echo Checking if port 5173 is available...
netstat -ano | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 5173 is already in use!
    echo Please close any existing frontend server first.
    pause
    exit /b 1
)

echo.
echo ✅ Ports are available
echo.
echo Starting Backend Server (Port 8080)...
start "Pathfinder Backend" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --reload --host 127.0.0.1 --port 8080"

echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend Server (Port 5173)...
start "Pathfinder Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo    ✅ Both servers are starting!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8080
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8080/docs
echo.
echo Two terminal windows should have opened.
echo Close those windows to stop the servers.
echo ========================================
echo.
pause
