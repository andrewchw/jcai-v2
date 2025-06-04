#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Restarts the Python server with proper environment activation
.DESCRIPTION
    This script stops any running Python server processes and starts a new one
    with the correct virtual environment activated
#>

# Set execution policy for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "🔄 Restarting the Python server..." -ForegroundColor Cyan

# Move to the project root directory
Push-Location -Path $PSScriptRoot

try {
    # Kill any existing server processes
    Write-Host "Stopping any existing Python server processes..." -ForegroundColor Yellow
    Get-Process -Name python | Where-Object { $_.CommandLine -like "*run.py*" } -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Activate virtual environment
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    if (Test-Path -Path ".\.venv\Scripts\Activate.ps1") {
        & ".\.venv\Scripts\Activate.ps1"
    } else {
        Write-Host "❌ Virtual environment not found! Creating one..." -ForegroundColor Red
        python -m venv .venv
        & ".\.venv\Scripts\Activate.ps1"
        pip install -r python-server\requirements.txt
    }

    # Start the server
    Write-Host "Starting Python server..." -ForegroundColor Green
    python python-server\run.py
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
} finally {
    # Restore original location
    Pop-Location
}
