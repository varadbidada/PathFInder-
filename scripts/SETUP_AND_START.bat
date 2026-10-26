@echo off
echo ========================================
echo    🚀 Pathfinder Complete Setup
echo ========================================

echo.
echo 📋 Checking system requirements...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Ollama not found. Installing Ollama for offline AI...
    echo.
    echo 📥 Downloading Ollama...
    
    REM Create temp directory
    if not exist temp mkdir temp
    
    REM Download Ollama
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'temp\OllamaSetup.exe' -UseBasicParsing } catch { Write-Host 'Download failed. Please install manually from https://ollama.com'; exit 1 }}"
    
    if exist temp\OllamaSetup.exe (
        echo ✅ Download complete
        echo 🚀 Installing Ollama...
        echo Please follow the installation wizard and then press any key to continue.
        start /wait temp\OllamaSetup.exe
        
        echo.
        echo ⏳ Waiting for Ollama service to start...
        timeout /t 10 /nobreak >nul
        
        REM Clean up
        rmdir /s /q temp
        
        echo 📦 Installing AI model (mistral - recommended for 16GB+ RAM)...
        echo This will download ~4GB. Please wait...
        ollama pull mistral
        
        if %errorlevel% equ 0 (
            echo ✅ Mistral model installed successfully
        ) else (
            echo ⚠️  Mistral failed. Trying smaller model (llama3.2:3b)...
            ollama pull llama3.2:3b
        )
        
    ) else (
        echo ❌ Download failed. Please install Ollama manually:
        echo 1. Go to https://ollama.com
        echo 2. Download and install Ollama
        echo 3. Run: ollama pull mistral
        echo 4. Then run this script again
        pause
        exit /b 1
    )
) else (
    echo ✅ Ollama found
    
    REM Check if any models are installed
    ollama list | findstr /C:"NAME" >nul 2>&1
    if %errorlevel% neq 0 (
        echo 📦 No models found. Installing mistral...
        ollama pull mistral
    ) else (
        echo ✅ Ollama models available
    )
)

echo.
echo 🔧 Installing backend dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Backend dependency installation failed
    pause
    exit /b 1
)
cd ..

echo.
echo 🎨 Installing frontend dependencies...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo ❌ Frontend dependency installation failed
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo    🚀 Starting Pathfinder System
echo ========================================

REM Check if backend is already running
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔧 Starting Backend Server...
    start "Pathfinder Backend" cmd /k "cd backend && echo Starting Pathfinder Backend... && python main.py"
    echo ⏳ Waiting for backend to start...
    timeout /t 8 /nobreak >nul
) else (
    echo ✅ Backend already running
)

echo 🎨 Starting Frontend Server...
start "Pathfinder Frontend" cmd /k "cd frontend && echo Starting Pathfinder Frontend... && npm run dev"

echo.
echo ⏳ Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo.
echo 🧪 Testing system...
python test_frontend_backend_connection.py

echo.
echo ========================================
echo    🎉 Pathfinder is Ready!
echo ========================================
echo.
echo 🌐 Open your browser and go to:
echo    http://localhost:5173
echo.
echo 📊 Backend API: http://127.0.0.1:8000
echo 📚 API Docs:   http://127.0.0.1:8000/docs
echo 🤖 LLM Status: http://127.0.0.1:8000/api/llm-status
echo.
echo 💡 Tips:
echo - Use the Debug Panel (🐛 button) to troubleshoot issues
echo - Ollama provides offline AI capabilities
echo - Check LLM status in the top-right corner
echo.
echo Press any key to open the application...
pause >nul

REM Open the application
start http://localhost:5173