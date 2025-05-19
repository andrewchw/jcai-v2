@echo off
echo ===========================================
echo   Starting the FastAPI server using the virtual environment...
echo ===========================================
echo.
echo Checking Python virtual environment...
if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found!
    echo Creating a new virtual environment...
    python -m venv .venv
    if ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment.
        echo Please make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    .\.venv\Scripts\pip install -r python-server\requirements.txt
    if ERRORLEVEL 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created and dependencies installed.
)

echo.
echo Starting server on http://localhost:8000
echo Press CTRL+C to stop the server
echo.
.\.venv\Scripts\python -m uvicorn python-server.app.main:app --reload --host 0.0.0.0 --port 8000
