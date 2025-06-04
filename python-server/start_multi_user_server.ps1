# PowerShell script to start the server with multi-user support
Write-Host "Setting up multi-user environment for Jira Chatbot API..." -ForegroundColor Cyan

# Create data directory if it doesn't exist
$dataDir = Join-Path $PSScriptRoot "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "Created data directory: $dataDir" -ForegroundColor Green
}

# Generate encryption key if not present
$keyFile = Join-Path $dataDir "encryption_key.txt"
if (-not (Test-Path $keyFile)) {
    # We'll let the application generate it on startup
    Write-Host "Encryption key will be generated on startup" -ForegroundColor Yellow
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Cyan
try {
    python -c "from app.core.init_db import init_db; init_db()"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database initialized successfully" -ForegroundColor Green
    } else {
        Write-Host "Database initialization failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "Error initializing database: $_" -ForegroundColor Red
}

# Start server with environment variables
Write-Host "Starting server with multi-user support..." -ForegroundColor Cyan

# Check if we're in a virtual environment
$inVenv = (Test-Path env:VIRTUAL_ENV)
if (-not $inVenv) {
    Write-Host "Warning: Not running in a virtual environment" -ForegroundColor Yellow
    Write-Host "Consider activating a virtual environment first" -ForegroundColor Yellow

    # Check if venv directory exists
    if (Test-Path (Join-Path $PSScriptRoot "..\env")) {
        Write-Host "Virtual environment found at ..\env" -ForegroundColor Cyan
        Write-Host "You can activate it with: ..\env\Scripts\Activate.ps1" -ForegroundColor Cyan
    }
}

# Set environment variables
$env:JIRA_ENABLE_MULTI_USER = "true"

# Run the application
Write-Host "Running uvicorn server..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
