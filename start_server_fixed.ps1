# Start Server with Proper Virtual Environment Activation
# This script will activate the correct virtual environment and start the server

$ErrorActionPreference = "Stop"

Write-Host "Starting JIRA Chatbot Server..." -ForegroundColor Green

# Check for which virtual environment exists and use the appropriate one
$venvPath = $null

if (Test-Path -Path "c:\Users\deencat\Documents\jcai-v2\.venv") {
    $venvPath = ".venv"
    Write-Host "Using .venv virtual environment" -ForegroundColor Cyan
} elseif (Test-Path -Path "c:\Users\deencat\Documents\jcai-v2\env") {
    $venvPath = "env"
    Write-Host "Using env virtual environment" -ForegroundColor Cyan
} else {
    Write-Host "No virtual environment found. Please create one first." -ForegroundColor Red
    exit 1
}

# Navigate to the project root
Set-Location "c:\Users\deencat\Documents\jcai-v2"

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if ($venvPath -eq ".venv") {
    & ".\.venv\Scripts\Activate.ps1"
} else {
    & ".\env\Scripts\Activate.ps1"
}

# Check if activation was successful
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Failed to activate virtual environment. Please check your setup." -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment activated successfully: $env:VIRTUAL_ENV" -ForegroundColor Green

# Navigate to the Python server directory
Set-Location "python-server"

# Start the server
Write-Host "Starting server..." -ForegroundColor Yellow
python run.py

# Handle any errors
if ($LASTEXITCODE -ne 0) {
    Write-Host "Server failed to start with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
