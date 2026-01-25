@echo off
TITLE AI Resume Critiquer
COLOR 0A

echo ==================================================
echo      STARTING LOCAL AI RESUME CRITIQUER
echo ==================================================
echo.

echo [1/3] Checking if Ollama is running...
tasklist /FI "IMAGENAME eq ollama_app.exe" 2>NUL | find /I /N "ollama_app.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo    -- Ollama is running. Good.
) else (
    echo    -- Starting Ollama...
    start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"
)

echo [2/3] Starting Python Backend...
echo    -- Access limited to this computer (Secure).
echo.

:: Start server on localhost (127.0.0.1) only
start cmd /k "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: Wait a moment for server to boot
timeout /t 3 >nul

echo [3/3] Opening Application...
start index.html

pause