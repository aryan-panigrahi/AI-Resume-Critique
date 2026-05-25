@echo off
TITLE AI Resume Critiquer
COLOR 0A

echo ==================================================
echo      STARTING LOCAL AI RESUME CRITIQUER
echo ==================================================
echo.

echo [1/3] Checking if Ollama is running...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
set OLLAMA_RUNNING=%ERRORLEVEL%
if "%OLLAMA_RUNNING%" NEQ "0" (
    tasklist /FI "IMAGENAME eq ollama_app.exe" 2>NUL | find /I /N "ollama_app.exe">NUL
    set OLLAMA_RUNNING=%ERRORLEVEL%
)

if "%OLLAMA_RUNNING%"=="0" (
    echo    -- Ollama is running. Good.
) else (
    echo    -- Starting Ollama...
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe" (
        start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"
    ) else (
        start /b "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe" serve
    )
)

echo [2/3] Starting Python Backend...
echo    -- Access limited to this computer (Secure).
echo.

:: Start server using the virtual environment
if exist .venv\Scripts\uvicorn.exe (
    start cmd /k ".venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
) else (
    start cmd /k "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

:: Wait a moment for server to boot
timeout /t 3 >nul

echo [3/3] Opening Application...
start index.html

pause