@echo off
echo ========================================
echo    Stopping Pathfinder Servers
echo ========================================
echo.

echo Stopping processes on port 8080 (Backend)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping processes on port 5173 (Frontend)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✅ Servers stopped
echo.
pause
