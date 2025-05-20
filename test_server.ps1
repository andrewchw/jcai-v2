#!/usr/bin/env pwsh
# Simple Server Test Script

# Set execution policy for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "Testing server connection..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    Write-Host "Server responded with status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response content:" -ForegroundColor Cyan
    $response.Content
    
    Write-Host "`nTesting OAuth token status..." -ForegroundColor Cyan
    $tokenResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/oauth/token/status" -UseBasicParsing -TimeoutSec 5
    Write-Host "Token status response:" -ForegroundColor Green
    $tokenResponse.Content
} catch {
    Write-Host "Error connecting to server: $_" -ForegroundColor Red
}
