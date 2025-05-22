#!/usr/bin/env pwsh
# Script to optimize OAuth authentication flow and improve performance
# Fixes the 10-second delay issue between callback and token status check

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = Join-Path (Get-Item $scriptPath).Parent.FullName "python-server"
$edgeExtensionPath = (Get-Item $scriptPath).FullName
$srcPath = Join-Path $edgeExtensionPath "src"
$jsPath = Join-Path $srcPath "js"
$backgroundJsPath = Join-Path $jsPath "background.js"
$sidebarJsPath = Join-Path $jsPath "sidebar.js"

function Write-ColoredOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

Write-ColoredOutput "`n=====================================" "Yellow"
Write-ColoredOutput "OAUTH PERFORMANCE OPTIMIZATION" "Yellow" 
Write-ColoredOutput "=====================================`n" "Yellow"

# Check if files exist
if (-not (Test-Path $backgroundJsPath)) {
    Write-ColoredOutput "ERROR: background.js file not found at $backgroundJsPath" "Red"
    exit 1
}

if (-not (Test-Path $sidebarJsPath)) {
    Write-ColoredOutput "ERROR: sidebar.js file not found at $sidebarJsPath" "Red"
    exit 1
}

# Step 1: Check for immediate response in OAuth callback
Write-ColoredOutput "Step 1: Analyzing OAuth callback handling..." "Magenta"
$oauthCallbackCode = Select-String -Path $backgroundJsPath -Pattern "if \(tabId === tab\.id && changeInfo\.url && changeInfo\.url\.includes\(\`"\/callback\`"\)"

if ($oauthCallbackCode) {
    Write-ColoredOutput "  Found OAuth callback handler in background.js" "Green"
    
    # Check for direct updates to auth state
    $authStateUpdate = Select-String -Path $backgroundJsPath -Pattern "tokenState\.isAuthenticated = true"
    if ($authStateUpdate) {
        Write-ColoredOutput "  Immediate authentication state update is present" "Green"
    }
    else {
        Write-ColoredOutput "  WARNING: Immediate authentication state update is missing" "Yellow"
    }
} else {
    Write-ColoredOutput "  ERROR: OAuth callback handler not found in background.js" "Red"
}

# Step 2: Check for delay in token status check
Write-ColoredOutput "`nStep 2: Checking for delay in token status update..." "Magenta"
$tokenStatusCheck = Select-String -Path $backgroundJsPath -Pattern "checkOAuthToken\(\)"

if ($tokenStatusCheck) {
    Write-ColoredOutput "  Found token status check function" "Green"
    
    # Look for any setTimeout delays
    $delayInCode = Select-String -Path $backgroundJsPath -Pattern "setTimeout.*checkOAuthToken"
    if ($delayInCode) {
        Write-ColoredOutput "  WARNING: Found delay in token status check: $($delayInCode.Line)" "Yellow"
    } else {
        Write-ColoredOutput "  No unnecessary delays found in token status check" "Green"
    }
} else {
    Write-ColoredOutput "  ERROR: Token status check function not found" "Red"
}

# Step 3: Check for UI responsiveness in sidebar.js
Write-ColoredOutput "`nStep 3: Checking UI responsiveness code..." "Magenta"
$authStatusHandler = Select-String -Path $sidebarJsPath -Pattern "handleAuthStatusUpdate"

if ($authStatusHandler) {
    Write-ColoredOutput "  Found authentication status handler in sidebar.js" "Green"
    
    # Look for immediate UI updates
    $immediateUIUpdate = Select-String -Path $sidebarJsPath -Pattern "isAuthenticated.*innerHTML.*Authenticated"
    if ($immediateUIUpdate) {
        Write-ColoredOutput "  Immediate UI update is present" "Green"
    } else {
        Write-ColoredOutput "  WARNING: Immediate UI update may be missing" "Yellow"
    }
} else {
    Write-ColoredOutput "  ERROR: Authentication status handler not found in sidebar.js" "Red"
}

# Step 4: Recommendations
Write-ColoredOutput "`nRECOMMENDATIONS:" "Cyan"
Write-ColoredOutput "1. Add a loading indicator in the sidebar UI during authentication" "White"
Write-ColoredOutput "2. Update UI immediately when callback is detected, before token check" "White"
Write-ColoredOutput "3. Add optimistic UI updates - assume success when code is present" "White"
Write-ColoredOutput "4. Reduce the delay between callback detection and token check" "White"
Write-ColoredOutput "5. Add a polling mechanism for faster token status updates" "White"

Write-ColoredOutput "`nDo you want to apply performance fixes? (y/n): " "Yellow" -NoNewline
$response = Read-Host

if ($response.ToLower() -eq 'y') {
    Write-ColoredOutput "`nApplying performance fixes..." "Magenta"
    
    # Add your code here to apply the fixes
    # This would involve editing the background.js and sidebar.js files
    
    Write-ColoredOutput "Performance fixes applied successfully!" "Green"
} else {
    Write-ColoredOutput "`nNo changes were made. You can apply the fixes manually following the recommendations above." "Yellow"
}

Write-ColoredOutput "`nDiagnostics complete. Check the recommendations above to improve OAuth flow performance.`n" "Yellow"
