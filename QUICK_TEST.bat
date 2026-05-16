@echo off
echo 🧪 Quick Pathfinder Test
echo ========================

echo.
echo 1. Testing Ollama...
"C:\Users\theva\AppData\Local\Programs\Ollama\ollama.exe" list
echo.

echo 2. Testing Backend LLM Integration...
cd backend
python -c "from services.llm_client import check_llm_health; import json; print('LLM Status:'); print(json.dumps(check_llm_health(), indent=2))"
cd ..
echo.

echo 3. Testing Complete Chat Flow...
python test_chat_flow.py

echo.
echo Test complete!
pause