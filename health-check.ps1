# JCAI Health Check Script - Auto-generated
Write-Host "?? JCAI System Health Check" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Extension Status
Write-Host "Extension Files:" -ForegroundColor Yellow
if (Test-Path "edge-extension\src\manifest.json") { Write-Host "  ??Manifest" -ForegroundColor Green } else { Write-Host "  ??Manifest" -ForegroundColor Red }
if (Test-Path "edge-extension\src\js\background.js") { Write-Host "  ??Background Script" -ForegroundColor Green } else { Write-Host "  ??Background Script" -ForegroundColor Red }
if (Test-Path "edge-extension\src\js\content-enhanced.js") { Write-Host "  ??Content Script" -ForegroundColor Green } else { Write-Host "  ??Content Script" -ForegroundColor Red }

# Server Status
Write-Host "Server Files:" -ForegroundColor Yellow
if (Test-Path "python-server\app\main.py") { Write-Host "  ??Main Server" -ForegroundColor Green } else { Write-Host "  ??Main Server" -ForegroundColor Red }
if (Test-Path "python-server\app\services\notification_service.py") { Write-Host "  ??Notification Service" -ForegroundColor Green } else { Write-Host "  ??Notification Service" -ForegroundColor Red }

Write-Host "
To run full diagnostic: .\check-source-code.ps1" -ForegroundColor Cyan
Write-Host "To validate and fix: .\validate-and-fix.ps1" -ForegroundColor Cyan
