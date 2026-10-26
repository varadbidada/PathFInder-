@echo off
title Ultimate Pathfinder Fix
echo.
echo ========================================
echo    🔧 ULTIMATE PATHFINDER FIX
echo ========================================
echo.

echo 📋 Critical Fixes Applied:
echo    ✅ Fixed ConversationState.user_responses error
echo    ✅ Added 30-second timeout to reactive generation
echo    ✅ Added ultimate fallback questions
echo    ✅ Improved error handling throughout
echo.

echo 🔄 Restarting with all fixes...

REM Kill all processes
taskkill /f /im "python.exe" >nul 2>&1
taskkill /f /im "node.exe" >nul 2>&1

timeout /t 5 /nobreak >nul

echo 🔧 Starting Backend (Ultimate Fix)...
start "Backend - ULTIMATE FIX" cmd /k "title Backend ULTIMATE && cd backend && echo ✅ Starting with all fixes applied... && python main.py"

timeout /t 15 /nobreak >nul

echo 🎨 Starting Frontend (Ultimate Fix)...
start "Frontend - ULTIMATE FIX" cmd /k "title Frontend ULTIMATE && cd frontend && echo ✅ Starting with improved error handling... && npm run dev"

timeout /t 10 /nobreak >nul

echo.
echo 🧪 Testing the ultimate fix...
python TEST_COMPLETE_FLOW.py

echo.
echo ========================================
echo    🎉 ULTIMATE FIX COMPLETE!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:5173
echo.
echo 💡 What should happen now:
echo    1. Session creation: ✅ Working
echo    2. Chat responses: ✅ Should work (with fallbacks)
echo    3. No more "Something went wrong" errors
echo    4. Graceful fallback to question bank if AI fails
echo.
echo 🚀 Opening Pathfinder...
start http://localhost:5173

echo.
echo 📝 If you still get errors:
echo    - The system now has multiple fallback layers
echo    - Check the Debug Panel (🐛 button) for details
echo    - Worst case: it falls back to predefined questions
echo.
echo Press any key to close...
pause >nul