# Debug Extension Detection Script
# This script helps debug why the extension bridge is not being detected

Write-Host "🔍 JCAI Extension Detection Debug Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Start the test server
Write-Host "`n1. Starting test server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd 'c:\Users\deencat\Documents\jcai-v2\edge-extension'; python -m http.server 8080" -WindowStyle Minimized

Start-Sleep 2

Write-Host "2. Opening test page in Edge..." -ForegroundColor Yellow
Start-Process msedge -ArgumentList "http://localhost:8080/test-extension-notifications.html"

Write-Host "`n3. Debug Steps to Follow:" -ForegroundColor Green
Write-Host "   a) Press F12 to open Developer Tools" -ForegroundColor White
Write-Host "   b) Go to Console tab" -ForegroundColor White
Write-Host "   c) Look for these messages:" -ForegroundColor White
Write-Host "      - 'JCAI Enhanced Content Script loaded'" -ForegroundColor Gray
Write-Host "      - 'JCAI Extension Bridge loaded and available!'" -ForegroundColor Gray
Write-Host "      - Any error messages" -ForegroundColor Gray
Write-Host "   d) In console, type: window.jcaiExtensionBridge" -ForegroundColor White
Write-Host "      This should show the bridge object if available" -ForegroundColor Gray

Write-Host "`n4. Extension Check:" -ForegroundColor Green
Write-Host "   a) Go to edge://extensions/" -ForegroundColor White
Write-Host "   b) Make sure JIRA Chatbot Assistant is enabled" -ForegroundColor White
Write-Host "   c) Click 'Reload' if needed" -ForegroundColor White
Write-Host "   d) Check that the extension has permissions for localhost" -ForegroundColor White

Write-Host "`n5. If extension bridge is still not detected:" -ForegroundColor Red
Write-Host "   a) Try refreshing the page (F5)" -ForegroundColor White
Write-Host "   b) Check if content script is running on localhost" -ForegroundColor White
Write-Host "   c) Look for CSP (Content Security Policy) errors" -ForegroundColor White

Write-Host "`nPress any key to stop the server when done testing..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the server
Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -like "*http.server*"} | Stop-Process -Force
Write-Host "Server stopped." -ForegroundColor Green
