@echo off
echo ========================================
echo    Starting Pathfinder API Server
echo ========================================
echo.
echo Server will start on: http://127.0.0.1:8081
echo API Documentation: http://127.0.0.1:8081/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8081
