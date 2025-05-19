# Server Startup Script for the Microsoft Edge Chatbot Extension for Jira
# This script activates the Python virtual environment and starts the FastAPI server

# Navigate to the python-server directory
Set-Location -Path ".\python-server"

# Activate the virtual environment
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Error: Virtual environment not found. Please run setup first." -ForegroundColor Red
    exit 1
}

# Check if the .env file exists
if (-not (Test-Path ".\.env")) {
    Write-Host "Warning: .env file not found. Creating a template .env file..." -ForegroundColor Yellow
    Copy-Item -Path ".\.env.example" -Destination ".\.env" -ErrorAction SilentlyContinue
    Write-Host "Please update the .env file with your credentials." -ForegroundColor Yellow
}

# Start the server
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "The server will be available at http://localhost:8000" -ForegroundColor Green
Write-Host "OAuth Token Dashboard: http://localhost:8000/dashboard/token" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "To stop the server, press CTRL+C" -ForegroundColor Yellow
python run.py

# Deactivate the virtual environment (this will only run if the server is stopped normally)
deactivate
Write-Host "Server stopped." -ForegroundColor Red
