@echo off
echo ========================================
echo    Checking Pathfinder Servers
echo ========================================
echo.

echo Checking Backend (Port 8080)...
netstat -ano | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo ✅ Backend is RUNNING on port 8080
) else (
    echo ❌ Backend is NOT running on port 8080
)

echo.
echo Checking Frontend (Port 5173)...
netstat -ano | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo ✅ Frontend is RUNNING on port 5173
) else (
    echo ❌ Frontend is NOT running on port 5173
)

echo.
echo Testing Backend API...
curl -s http://127.0.0.1:8080/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is responding
) else (
    echo ❌ Backend API is not responding
)

echo.
echo ========================================
echo.
pause
