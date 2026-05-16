# Start Backend Server
Write-Host "Starting Backend Server on http://127.0.0.1:8080" -ForegroundColor Green
Set-Location backend
uvicorn main:app --reload --host 127.0.0.1 --port 8080
