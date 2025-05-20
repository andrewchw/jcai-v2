# Enable script execution for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activate virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# Change directory to python-server
Write-Host "Changing to python-server directory..." -ForegroundColor Green
Push-Location -Path "python-server"

try {
    # Run the token cleanup script
    Write-Host "Cleaning up OAuth tokens..." -ForegroundColor Green
    python cleanup_tokens.py
}
finally {
    # Return to original directory
    Pop-Location
}
