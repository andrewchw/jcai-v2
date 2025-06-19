# Extension Reload Helper Script
# This script provides instructions for reloading the JCAI extension

Write-Host "🔄 JCAI Extension Reload Helper" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

Write-Host "`n📋 Step-by-Step Extension Reload Instructions:" -ForegroundColor Yellow

Write-Host "`n1. Open Edge Extension Management:" -ForegroundColor Green
Write-Host "   - Press Ctrl+Shift+I (or F12) to open DevTools" -ForegroundColor White
Write-Host "   - OR navigate to: edge://extensions/" -ForegroundColor White

Write-Host "`n2. Find JIRA Chatbot Assistant Extension:" -ForegroundColor Green
Write-Host "   - Look for the JCAI extension in the list" -ForegroundColor White
Write-Host "   - Make sure the toggle is ON (enabled)" -ForegroundColor White

Write-Host "`n3. Reload the Extension:" -ForegroundColor Green
Write-Host "   - Click the 'Reload' button under the extension" -ForegroundColor White
Write-Host "   - Wait for it to finish reloading" -ForegroundColor White

Write-Host "`n4. Verify Extension Path:" -ForegroundColor Green
Write-Host "   - Extension should be loaded from:" -ForegroundColor White
Write-Host "     c:\Users\deencat\Documents\jcai-v2\edge-extension\src" -ForegroundColor Gray

Write-Host "`n5. Test the Extension:" -ForegroundColor Green
Write-Host "   - Go to: http://localhost:8080/simple-bridge-test.html" -ForegroundColor White
Write-Host "   - OR go to: http://localhost:8080/test-extension-notifications.html" -ForegroundColor White
Write-Host "   - Press F12, go to Console tab" -ForegroundColor White
Write-Host "   - Look for 'JCAI Enhanced Content Script loaded successfully'" -ForegroundColor White

Write-Host "`n6. Check Browser Console:" -ForegroundColor Green
Write-Host "   - If you see errors, the extension needs fixing" -ForegroundColor White
Write-Host "   - If you see 'Extension context not available', try reloading again" -ForegroundColor White
Write-Host "   - Look for: 'JCAI Extension Bridge loaded and available!'" -ForegroundColor White

Write-Host "`n7. Test the Bridge:" -ForegroundColor Green
Write-Host "   - In browser console, type: window.jcaiExtensionBridge" -ForegroundColor White
Write-Host "   - Should show an object with isExtensionAvailable: true" -ForegroundColor White

Write-Host "`n❗ Common Issues:" -ForegroundColor Red
Write-Host "   - Extension not enabled: Enable it in edge://extensions/" -ForegroundColor White
Write-Host "   - Wrong path: Make sure extension loads from the src folder" -ForegroundColor White
Write-Host "   - Cache issues: Try Ctrl+Shift+R to hard refresh the test page" -ForegroundColor White
Write-Host "   - Permission issues: Make sure extension has localhost permissions" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "`n✅ Follow these steps and the extension should work!" -ForegroundColor Green
