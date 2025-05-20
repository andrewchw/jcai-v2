# Enable script execution for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activate virtual environment
Write-Host "=== Starting environment validation ===" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version | Out-String
    Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ and add it to PATH." -ForegroundColor Red
}

# Check Node.js installation
try {
    $nodeVersion = node --version | Out-String
    $npmVersion = npm --version | Out-String
    Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
    Write-Host "✅ npm installed: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js and add it to PATH." -ForegroundColor Red
}

# Check virtual environment
if (Test-Path ".\.venv") {
    Write-Host "✅ Python virtual environment exists" -ForegroundColor Green
    
    # Activate the environment to check packages
    try {
        & ".\.venv\Scripts\Activate.ps1"
        Write-Host "✅ Successfully activated virtual environment" -ForegroundColor Green
        
        # Check Python packages
        Write-Host "Checking installed packages..." -ForegroundColor Yellow
        pip list | Select-String -Pattern "fastapi|uvicorn|requests|python-dotenv"
    } catch {
        Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Python virtual environment not found. Please run setup_environment.ps1" -ForegroundColor Red
}

# Check for .env file
if (Test-Path ".\.env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found. Please create a .env file with necessary settings" -ForegroundColor Red
}

# Check for OAuth token file
if (Test-Path ".\python-server\oauth_token.json") {
    Write-Host "✅ OAuth token file exists" -ForegroundColor Green
} else {
    Write-Host "⚠️ OAuth token file not found. You may need to authenticate with JIRA" -ForegroundColor Yellow
}

# Check if port 8000 is available
try {
    $portInUse = $null
    $portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    
    if ($portInUse) {
        Write-Host "⚠️ Port 8000 is already in use by another process (PID: $($portInUse.OwningProcess))" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Port 8000 is available for the server" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Could not check port availability" -ForegroundColor Yellow
}

Write-Host "`n=== Validation complete ===" -ForegroundColor Cyan
Write-Host "To start the server, run: .\run_server_fixed.ps1" -ForegroundColor Yellow
Write-Host "For more tools, run: .\jcai-tools.ps1" -ForegroundColor Yellow
