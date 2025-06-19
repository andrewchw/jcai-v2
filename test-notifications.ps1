# Browser Notification Test Script for JCAI
# This script helps you test the browser notification system

Write-Host "🔔 JCAI Browser Notification Test Guide" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "🔍 Checking if server is running..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -Method GET -ErrorAction Stop
    Write-Host "✅ Server is running!" -ForegroundColor Green
    $healthData = $healthCheck.Content | ConvertFrom-Json
    Write-Host "   Status: $($healthData.status)" -ForegroundColor Gray
    Write-Host "   Version: $($healthData.version)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Server is not running! Please start the server first:" -ForegroundColor Red
    Write-Host "   cd python-server" -ForegroundColor Yellow
    Write-Host "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "🎯 Test Steps:" -ForegroundColor Cyan
Write-Host "1. Install Edge Extension (if not already done)" -ForegroundColor White
Write-Host "2. Open the test page in your browser" -ForegroundColor White
Write-Host "3. Follow the step-by-step tests on the page" -ForegroundColor White
Write-Host ""

# Open the test page
$testPagePath = Join-Path $PWD "test-browser-notifications.html"
Write-Host "🌐 Opening test page..." -ForegroundColor Yellow
Write-Host "   File: $testPagePath" -ForegroundColor Gray

try {
    Start-Process "msedge.exe" "file:///$($testPagePath.Replace('\', '/'))"
    Write-Host "✅ Test page opened in Edge!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not auto-open Edge. Please manually open:" -ForegroundColor Yellow
    Write-Host "   file:///$($testPagePath.Replace('\', '/'))" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📋 Extension Installation Steps (if needed):" -ForegroundColor Cyan
Write-Host "1. Open Edge and go to: edge://extensions/" -ForegroundColor White
Write-Host "2. Enable 'Developer mode' (bottom-left toggle)" -ForegroundColor White
Write-Host "3. Click 'Load unpacked'" -ForegroundColor White
Write-Host "4. Select folder: $PWD\edge-extension\src" -ForegroundColor White
Write-Host ""

Write-Host "🔔 Quick API Tests:" -ForegroundColor Cyan
$testUserId = "edge-1749460706591-hh3bdgu8"

# Test creating a browser notification
Write-Host "   Creating test browser notification..." -ForegroundColor Yellow
try {
    $createResult = Invoke-WebRequest -Uri "http://localhost:8000/api/notifications/browser/test/$testUserId" -Method POST
    $createData = $createResult.Content | ConvertFrom-Json
    if ($createData.success) {
        Write-Host "   ✅ Browser notification created: $($createData.notification_id)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to create notification" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error creating notification: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Jira notification
Write-Host "   Testing Jira notification..." -ForegroundColor Yellow
try {
    $jiraResult = Invoke-WebRequest -Uri "http://localhost:8000/api/notifications/jira/test/$testUserId" -Method POST
    $jiraData = $jiraResult.Content | ConvertFrom-Json
    if ($jiraData.test_result.success) {
        Write-Host "   ✅ Jira notification sent (check JCAI-124 comments)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Jira notification failed: $($jiraData.test_result.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error testing Jira notification: $($_.Exception.Message)" -ForegroundColor Red
}

# Check pending notifications
Write-Host "   Checking pending notifications..." -ForegroundColor Yellow
try {
    $pendingResult = Invoke-WebRequest -Uri "http://localhost:8000/api/notifications/browser/pending/$testUserId" -Method GET
    $pendingData = $pendingResult.Content | ConvertFrom-Json
    Write-Host "   📥 Pending notifications: $($pendingData.total_count)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error checking pending notifications: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Use the test page to interactively test notifications" -ForegroundColor White
Write-Host "2. Make sure notification permissions are granted in Edge" -ForegroundColor White
Write-Host "3. Check the browser extension is loaded and working" -ForegroundColor White
Write-Host "4. Test both browser and Jira notifications" -ForegroundColor White
Write-Host ""
Write-Host "📖 For more help, check the test page instructions!" -ForegroundColor Green
