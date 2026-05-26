@echo off
TITLE Scope
COLOR 0A

echo ==================================================
echo         STARTING SCOPE LOCAL AI CRITIQUER
echo ==================================================
echo.

echo [1/3] Checking if LM Studio Local Server is running...
curl -s -f -o NUL http://localhost:1234/v1/models
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ WARNING: LM Studio Local Server does not appear to be active at http://localhost:1234
    echo.
    echo Please follow these steps to start it:
    echo    1. Open LM Studio on your computer.
    echo    2. Load your desired LLM - such as Llama 3.1 or Qwen 2.5 - in the top bar.
    echo    3. Click on the "Local Server" tab - double-arrow icon - in the left sidebar.
    echo    4. Click the "Start Server" button - using default port 1234.
    echo.
    echo Once you have started the local server, press any key below to continue...
    pause >nul
    echo.
    echo    -- Proceeding with startup...
) else (
    echo    -- LM Studio Local Server is active and running. Good.
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
ping 127.0.0.1 -n 4 >nul

echo [3/3] Opening Application...
start index.html

pause