# Test Authentication Flow
# This script will restart the server and verify it's running correctly

# Stop any existing Python processes (that might be running the server)
Write-Host "Stopping any existing Python processes..." -ForegroundColor Yellow
Stop-Process -Name python -ErrorAction SilentlyContinue

# Navigate to server directory
Write-Host "Changing to server directory..." -ForegroundColor Yellow
cd "c:\Users\deencat\Documents\jcai-v2\python-server"

# Verify environment
Write-Host "Checking environment..." -ForegroundColor Yellow
if (Test-Path "env\Scripts\activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    . .\env\Scripts\activate.ps1
} else {
    Write-Host "Virtual environment not found. Please set up environment first." -ForegroundColor Red
    exit 1
}

# Clean up any stale token if requested
if ($args -contains "-clean") {
    Write-Host "Cleaning up OAuth tokens..." -ForegroundColor Yellow
    if (Test-Path "oauth_token.json") {
        Rename-Item -Path "oauth_token.json" -NewName "oauth_token_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        Write-Host "Backed up and removed existing token file" -ForegroundColor Green
    }
}

# Start the server
Write-Host "Starting Python server..." -ForegroundColor Yellow
$pythonProcess = Start-Process -FilePath "python" -ArgumentList "-m app.main" -WorkingDirectory "." -PassThru -NoNewWindow

# Wait a moment for server to start
Start-Sleep -Seconds 2

# Check if server is running
if (!$pythonProcess.HasExited) {
    Write-Host "Server started successfully with PID $($pythonProcess.Id)" -ForegroundColor Green
    Write-Host "Server should be accessible at: http://localhost:8000" -ForegroundColor Cyan

    # Open health endpoint in browser to verify it's working
    Write-Host "Opening health endpoint in browser to verify..." -ForegroundColor Yellow
    Start-Process "http://localhost:8000/api/health"

    Write-Host "`nNext steps:" -ForegroundColor Green
    Write-Host "1. Reload your Edge extension" -ForegroundColor Cyan
    Write-Host "2. Open the sidebar and check connection status" -ForegroundColor Cyan
    Write-Host "3. Try the login flow" -ForegroundColor Cyan
    Write-Host "`nTo stop the server, press Ctrl+C in this window or run Stop-Process -Id $($pythonProcess.Id)" -ForegroundColor Yellow
} else {
    Write-Host "Failed to start server. Check for errors." -ForegroundColor Red
}

# Keep script running to see server output
Write-Host "`nServer is running. Press Ctrl+C to exit." -ForegroundColor Magenta
try {
    Wait-Process -Id $pythonProcess.Id
} catch {
    Write-Host "Server process ended." -ForegroundColor Red
}
