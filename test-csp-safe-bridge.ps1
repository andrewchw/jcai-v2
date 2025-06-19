# Test CSP-Safe Extension Bridge
Write-Host "🔧 JCAI CSP-Safe Extension Bridge Test" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

Write-Host "`n1. The extension has been updated with CSP-safe bridge" -ForegroundColor Green
Write-Host "   - Removed inline script injection" -ForegroundColor White
Write-Host "   - Using direct window assignment" -ForegroundColor White
Write-Host "   - Using custom events instead of postMessage" -ForegroundColor White

Write-Host "`n2. Next steps:" -ForegroundColor Yellow
Write-Host "   a) Go to edge://extensions/" -ForegroundColor White
Write-Host "   b) Find 'JIRA Chatbot Assistant'" -ForegroundColor White
Write-Host "   c) Click the 'Reload' button" -ForegroundColor White
Write-Host "   d) Refresh the test page" -ForegroundColor White

Write-Host "`n3. Testing the bridge:" -ForegroundColor Yellow
Write-Host "   a) Open browser console (F12)" -ForegroundColor White
Write-Host "   b) You should see: 'JCAI Extension Bridge loaded and available (CSP-safe)!'" -ForegroundColor White
Write-Host "   c) Type: window.jcaiExtensionBridge" -ForegroundColor White
Write-Host "   d) Click 'Run Full Test' button" -ForegroundColor White

Write-Host "`n4. What to expect:" -ForegroundColor Green
Write-Host "   - No CSP violations in console" -ForegroundColor White
Write-Host "   - Extension bridge should be detected" -ForegroundColor White
Write-Host "   - Test notifications should work" -ForegroundColor White

Write-Host "`n5. Starting test server..." -ForegroundColor Yellow
cd "c:\Users\deencat\Documents\jcai-v2\edge-extension"
Start-Process powershell -ArgumentList "-Command", "python -m http.server 8080" -WindowStyle Minimized

Start-Sleep 2

Write-Host "6. Opening test page..." -ForegroundColor Yellow
Start-Process msedge -ArgumentList "http://localhost:8080/simple-bridge-test.html"

Write-Host "`n✅ Test environment ready!" -ForegroundColor Green
Write-Host "Please reload the extension and refresh the test page." -ForegroundColor Cyan

Write-Host "`nPress any key to stop the server..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the server
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*http.server*" } | Stop-Process -Force
Write-Host "Server stopped." -ForegroundColor Green
