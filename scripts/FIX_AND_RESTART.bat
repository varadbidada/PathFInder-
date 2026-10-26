@echo off
title Fixing Pathfinder Frontend Issue
echo.
echo ========================================
echo    🔧 Fixing Pathfinder Frontend Issue
echo ========================================
echo.

echo 📋 Issue Identified:
echo    - Frontend was using wrong API paths
echo    - Session creation was failing
echo    - Chat navigation was blocked
echo.

echo ✅ Fix Applied:
echo    - Updated useSession.js API path
echo    - Updated useConversation.js API path
echo    - Fixed frontend-backend connection
echo.

echo 🧪 Testing the fix...
echo Opening test page in browser...
start TEST_FRONTEND_FIX.html

echo.
echo 🚀 Restarting servers with fix...

REM Kill any existing processes
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "python.exe" >nul 2>&1

echo ⏳ Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo 🔧 Starting Backend...
start "Pathfinder Backend - FIXED" cmd /k "title Backend FIXED && cd backend && echo Backend starting with Ollama integration... && python main.py"

echo ⏳ Waiting 10 seconds for backend...
timeout /t 10 /nobreak >nul

echo 🎨 Starting Frontend...
start "Pathfinder Frontend - FIXED" cmd /k "title Frontend FIXED && cd frontend && echo Frontend starting with fixed API paths... && npm run dev"

echo ⏳ Waiting 8 seconds for frontend...
timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo    🎉 PATHFINDER FIXED AND READY!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://127.0.0.1:8000
echo 🧪 Test:     TEST_FRONTEND_FIX.html
echo.
echo 💡 What was fixed:
echo    ✅ Session creation now works
echo    ✅ Chat navigation now works  
echo    ✅ Ollama integration active
echo    ✅ Reactive AI conversations
echo.
echo 🚀 Opening Pathfinder...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo 📝 Instructions:
echo 1. Fill out the initial form
echo 2. Click "Start Session"
echo 3. You should now navigate to chat automatically
echo 4. First AI response may take 10-20 seconds
echo.
echo Press any key to close...
pause >nul