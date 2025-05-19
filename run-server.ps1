Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  JIRA CHATBOT API SERVER" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating a new virtual environment..." -ForegroundColor Yellow
    
    try {
        python -m venv .venv
    } catch {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        Write-Host "Please make sure Python is installed and in your PATH." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    try {
        & ".\.venv\Scripts\pip" install -r python-server\requirements.txt
    } catch {
        Write-Host "[ERROR] Failed to install dependencies." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "[SUCCESS] Virtual environment created and dependencies installed." -ForegroundColor Green
}

# Run the verify environment script
Write-Host "Verifying environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\python" verify_env.py

# Start the server
Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs available at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Token Dashboard available at: http://localhost:8000/dashboard/token" -ForegroundColor Green
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Change to the python-server directory first to ensure correct paths
Push-Location -Path "python-server"
try {
    & ".\..\\.venv\Scripts\python" run.py
} finally {
    # Restore original directory when done
    Pop-Location
}
