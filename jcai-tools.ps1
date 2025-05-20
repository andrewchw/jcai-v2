# Master helper script for JCAI project

# Enable script execution for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

function Show-Menu {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "       JIRA CHATBOT ASSISTANT TOOLS     " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host
    Write-Host "1: Start Python Server"
    Write-Host "2: Run OAuth Troubleshooter"
    Write-Host "3: Clean Up OAuth Tokens"
    Write-Host "4: Test JIRA Connection"
    Write-Host "5: Check OAuth Token"
    Write-Host "6: Token Dashboard (requires server running)"
    Write-Host "Q: Quit"
    Write-Host
}

function Activate-Environment {
    # Activate virtual environment if it exists
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        & ".\.venv\Scripts\Activate.ps1"
        return $true
    } else {
        Write-Host "Virtual environment not found. Please run setup_environment.ps1 first." -ForegroundColor Red
        return $false
    }
}

function Start-PythonServer {
    if (Activate-Environment) {
        Push-Location -Path "python-server"
        try {
            Write-Host "Starting Python server..." -ForegroundColor Green
            Write-Host "Press Ctrl+C to stop the server when done."
            python run.py
        } finally {
            Pop-Location
        }
    }
}

function Run-OAuthTroubleshooter {
    if (Activate-Environment) {
        Push-Location -Path "python-server"
        try {
            Write-Host "Running OAuth troubleshooter..." -ForegroundColor Green
            python jira_oauth2_troubleshooter.py
        } finally {
            Pop-Location
        }
    }
}

function Clean-OAuthTokens {
    if (Activate-Environment) {
        Push-Location -Path "python-server"
        try {
            Write-Host "Cleaning up OAuth tokens..." -ForegroundColor Green
            python cleanup_tokens.py
        } finally {
            Pop-Location
        }
    }
}

function Test-JiraConnection {
    if (Activate-Environment) {
        Push-Location -Path "python-server"
        try {
            Write-Host "Testing JIRA connection..." -ForegroundColor Green
            python test_jira_connection.py
        } finally {
            Pop-Location
        }
    }
}

function Check-OAuthToken {
    if (Activate-Environment) {
        Push-Location -Path "python-server"
        try {
            Write-Host "Checking OAuth token..." -ForegroundColor Green
            python check_oauth_token.py
        } finally {
            Pop-Location
        }
    }
}

function Open-TokenDashboard {
    Start-Process "http://localhost:8000/dashboard/token"
    Write-Host "Opening Token Dashboard in browser. Make sure the server is running!" -ForegroundColor Yellow
}

# Main program loop
$running = $true
while ($running) {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" { Start-PythonServer }
        "2" { Run-OAuthTroubleshooter }
        "3" { Clean-OAuthTokens }
        "4" { Test-JiraConnection }
        "5" { Check-OAuthToken }
        "6" { Open-TokenDashboard }
        "q" { $running = $false }
        "Q" { $running = $false }
        default { Write-Host "Invalid choice. Please try again." -ForegroundColor Red }
    }
    
    if ($running -and $choice -ne "1") {
        Write-Host
        Read-Host "Press Enter to return to menu"
    }
}

Write-Host "Exiting..." -ForegroundColor Green
