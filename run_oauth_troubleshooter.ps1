# Enable script execution for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activate virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# Change directory to python-server
Write-Host "Changing to python-server directory..." -ForegroundColor Green
Push-Location -Path "python-server"

try {
    # Run the OAuth troubleshooter
    Write-Host "Starting OAuth troubleshooter..." -ForegroundColor Green
    python jira_oauth2_troubleshooter.py
}
finally {
    # Return to original directory
    Pop-Location
}
