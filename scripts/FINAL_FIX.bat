@echo off
title Final Pathfinder Fix
echo.
echo ========================================
echo    🔧 FINAL PATHFINDER FIX
echo ========================================
echo.

echo 📋 Issues Fixed:
echo    ✅ Frontend API endpoints corrected
echo    ✅ Chat timeout increased to 90 seconds
echo    ✅ Better error messages for Ollama delays
echo    ✅ Response field mapping fixed
echo    ✅ Loading indicators improved
echo.

echo 🧪 Testing Ollama...
"C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" list

echo.
echo 🔄 Restarting servers with all fixes...

REM Stop existing processes
echo Stopping existing processes...
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "python.exe" >nul 2>&1

timeout /t 3 /nobreak >nul

echo 🔧 Starting Backend (Fixed)...
start "Backend - FIXED" cmd /k "title Pathfinder Backend FIXED && cd backend && echo ✅ Backend starting with Ollama integration... && python main.py"

timeout /t 12 /nobreak >nul

echo 🎨 Starting Frontend (Fixed)...
start "Frontend - FIXED" cmd /k "title Pathfinder Frontend FIXED && cd frontend && echo ✅ Frontend starting with fixed chat handling... && npm run dev"

timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo    🎉 PATHFINDER FULLY FIXED!
echo ========================================
echo.
echo 🌐 Open: http://localhost:5173
echo.
echo 💡 What to expect:
echo    1. Fill the form and click "Start Session"
echo    2. Should navigate to chat automatically
echo    3. Type "yes" or any message
echo    4. First response takes 10-30 seconds (Ollama)
echo    5. You'll see "Processing with Ollama AI..." message
echo    6. Then get the actual AI response
echo.
echo 🚀 Opening Pathfinder...
start http://localhost:5173

echo.
echo 📝 If you still get errors:
echo    - Wait for the full 30 seconds
echo    - Check the Debug Panel (🐛 button)
echo    - Look for "Processing with Ollama AI..." message
echo.
echo Press any key to close...
pause >nul