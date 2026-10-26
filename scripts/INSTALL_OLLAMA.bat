@echo off
echo ========================================
echo    🤖 Installing Ollama for Offline AI
echo ========================================

echo.
echo 📥 Downloading Ollama installer...
echo Please wait while we download Ollama from https://ollama.com

REM Download Ollama installer
powershell -Command "& {Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'}"

if exist OllamaSetup.exe (
    echo ✅ Download complete!
    echo.
    echo 🚀 Starting Ollama installation...
    echo Please follow the installation wizard.
    start /wait OllamaSetup.exe
    
    echo.
    echo 🧹 Cleaning up installer...
    del OllamaSetup.exe
    
    echo.
    echo ⏳ Waiting for Ollama service to start...
    timeout /t 5 /nobreak >nul
    
    echo.
    echo 📦 Installing recommended model (mistral)...
    echo This may take a few minutes depending on your internet speed...
    ollama pull mistral
    
    echo.
    echo ✅ Ollama installation complete!
    echo.
    echo 🧪 Testing Ollama...
    ollama list
    
) else (
    echo ❌ Download failed. Please install manually:
    echo 1. Go to https://ollama.com
    echo 2. Download Ollama for Windows
    echo 3. Run the installer
    echo 4. Open command prompt and run: ollama pull mistral
)

echo.
echo ========================================
echo    Installation Complete
echo ========================================
pause