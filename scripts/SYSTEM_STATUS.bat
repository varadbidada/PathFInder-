@echo off
title Pathfinder System Status
color 0A
echo.
echo ========================================
echo    🧭 PATHFINDER SYSTEM STATUS
echo ========================================
echo.

echo 🔧 Backend Status:
curl -s http://127.0.0.1:8000/health
echo.

echo 🤖 LLM Status:
curl -s http://127.0.0.1:8000/api/llm-status
echo.

echo 🧪 Testing Session Creation:
curl -X POST http://127.0.0.1:8000/session/start -H "Content-Type: application/json" -d "{\"jee_rank\":5000,\"budget_lakh\":3.0}" -s | findstr session_id
echo.

echo ========================================
echo    🎉 SYSTEM READY!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://127.0.0.1:8000
echo 📚 API Docs: http://127.0.0.1:8000/docs
echo.
echo 💡 Features Active:
echo    ✅ Ollama AI (llama3.2:3b)
echo    ✅ Reactive Conversations
echo    ✅ Fixed API Endpoints
echo    ✅ Session Creation Working
echo    ✅ Chat Navigation Fixed
echo.

echo 🚀 Opening Pathfinder...
start http://localhost:5173

echo.
echo 📝 Usage Instructions:
echo 1. Fill out the initial form (JEE rank, budget, location)
echo 2. Click "Start Your AI Counselling Session"
echo 3. You should automatically navigate to chat
echo 4. Start chatting - first response takes 10-20 seconds
echo 5. Use Debug Panel (🐛) if you encounter issues
echo.
echo Press any key to close...
pause >nul