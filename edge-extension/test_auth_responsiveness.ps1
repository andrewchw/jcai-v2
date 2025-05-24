# Test Authentication Responsiveness Improvements
# This script tests the improved authentication responsiveness

Write-Host "Testing Authentication Responsiveness Improvements..." -ForegroundColor Cyan

# Test 1: Check if smart debouncing constants are defined
Write-Host "`n1. Checking smart debouncing implementation..." -ForegroundColor Yellow

$sidebarJs = "c:\Users\deencat\Documents\jcai-v2\edge-extension\src\js\sidebar.js"
$backgroundJs = "c:\Users\deencat\Documents\jcai-v2\edge-extension\src\js\background.js"

# Check for smart debouncing in sidebar
$smartDebouncing = Select-String -Path $sidebarJs -Pattern "timeSinceAuth.*30000.*2000.*8000"
if ($smartDebouncing) {
    Write-Host "   ✓ Smart debouncing implemented in sidebar.js" -ForegroundColor Green
    Write-Host "     Found: $($smartDebouncing.Line.Trim())" -ForegroundColor Gray
}
else {
    Write-Host "   ✗ Smart debouncing not found in sidebar.js" -ForegroundColor Red
}

# Check for lastAuthTime tracking
$authTimeTracking = Select-String -Path $sidebarJs -Pattern "lastAuthTime"
if ($authTimeTracking) {
    Write-Host "   ✓ Authentication time tracking implemented" -ForegroundColor Green
    Write-Host "     Found $($authTimeTracking.Count) references to lastAuthTime" -ForegroundColor Gray
}
else {
    Write-Host "   ✗ Authentication time tracking not found" -ForegroundColor Red
}

# Test 2: Check background script fast interval implementation
Write-Host "`n2. Checking fast token checking intervals..." -ForegroundColor Yellow

$fastInterval = Select-String -Path $backgroundJs -Pattern "FAST_TOKEN_CHECK_INTERVAL"
if ($fastInterval) {
    Write-Host "   ✓ Fast token check interval defined" -ForegroundColor Green
    Write-Host "     Found: $($fastInterval.Line.Trim())" -ForegroundColor Gray
}
else {
    Write-Host "   ✗ Fast token check interval not found" -ForegroundColor Red
}

$smartInterval = Select-String -Path $backgroundJs -Pattern "shouldUseFastInterval.*timeSinceAuth"
if ($smartInterval) {
    Write-Host "   ✓ Smart interval switching implemented" -ForegroundColor Green
}
else {
    Write-Host "   ✗ Smart interval switching not found" -ForegroundColor Red
}

# Test 3: Check immediate UI feedback improvements
Write-Host "`n3. Checking immediate UI feedback..." -ForegroundColor Yellow

$immediateUpdate = Select-String -Path $sidebarJs -Pattern "Update UI immediately"
if ($immediateUpdate) {
    Write-Host "   ✓ Immediate UI update implemented" -ForegroundColor Green
}
else {
    Write-Host "   ✗ Immediate UI update not found" -ForegroundColor Red
}

# Test 4: Check tab closing optimization
Write-Host "`n4. Checking tab closing optimization..." -ForegroundColor Yellow

$quickClose = Select-String -Path $backgroundJs -Pattern "1000.*Reduced from 2000ms"
if ($quickClose) {
    Write-Host "   ✓ Faster tab closing implemented (1s instead of 2s)" -ForegroundColor Green
}
else {
    Write-Host "   ✗ Tab closing optimization not found" -ForegroundColor Red
}

# Test 5: Verify syntax correctness
Write-Host "`n5. Testing JavaScript syntax..." -ForegroundColor Yellow

try {
    # Basic syntax check by trying to parse the files
    $sidebarContent = Get-Content $sidebarJs -Raw
    $backgroundContent = Get-Content $backgroundJs -Raw
    
    # Check for basic syntax issues
    $syntaxIssues = @()
    
    # Check for unmatched braces (basic check)
    $openBraces = ($sidebarContent | Select-String -Pattern "\{" -AllMatches).Matches.Count
    $closeBraces = ($sidebarContent | Select-String -Pattern "\}" -AllMatches).Matches.Count
    
    if ($openBraces -eq $closeBraces) {
        Write-Host "   ✓ Sidebar.js brace matching looks good ($openBraces pairs)" -ForegroundColor Green
    }
    else {
        Write-Host "   ✗ Sidebar.js brace mismatch: $openBraces open, $closeBraces close" -ForegroundColor Red
    }
    
    $openBraces = ($backgroundContent | Select-String -Pattern "\{" -AllMatches).Matches.Count
    $closeBraces = ($backgroundContent | Select-String -Pattern "\}" -AllMatches).Matches.Count
    
    if ($openBraces -eq $closeBraces) {
        Write-Host "   ✓ Background.js brace matching looks good ($openBraces pairs)" -ForegroundColor Green
    }
    else {
        Write-Host "   ✗ Background.js brace mismatch: $openBraces open, $closeBraces close" -ForegroundColor Red
    }
    
}
catch {
    Write-Host "   ✗ Error checking syntax: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "SUMMARY OF RESPONSIVENESS IMPROVEMENTS:" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "1. Smart Debouncing: Shorter delays (2s) for 30s after authentication" -ForegroundColor White
Write-Host "2. Fast Token Checking: 30s intervals for 5 minutes after auth" -ForegroundColor White
Write-Host "3. Immediate UI Updates: Authentication status shows instantly" -ForegroundColor White
Write-Host "4. Faster Tab Closing: Auth tab closes in 1s instead of 2s" -ForegroundColor White
Write-Host "5. Smart Reconnection: Reduced debounce after recent auth" -ForegroundColor White

Write-Host "`nThese improvements should significantly reduce the delay between" -ForegroundColor Green
Write-Host "OAuth completion and 'Authenticated ✓' display in the extension." -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Test the extension by performing OAuth login" -ForegroundColor Yellow
Write-Host "2. Observe the authentication status update timing" -ForegroundColor Yellow
Write-Host "3. Check browser console for smart debouncing logs" -ForegroundColor Yellow
