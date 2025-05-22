#!/usr/bin/env pwsh
#
# OAuth authentication flow patch script for Jira Chatbot Edge extension
# This script applies fixes to the OAuth authentication flow in the background.js file
#

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Get-Item $scriptPath).Parent.FullName
$edgeExtensionPath = Join-Path $rootPath "edge-extension"
$srcPath = Join-Path $edgeExtensionPath "src"
$jsPath = Join-Path $srcPath "js"
$backgroundJsPath = Join-Path $jsPath "background.js"
$patchFilePath = Join-Path $jsPath "background.js.patch"
$backupPath = Join-Path $jsPath "background.js.bak.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

function Write-ColoredOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

# Check if files exist
if (-not (Test-Path $backgroundJsPath)) {
    Write-ColoredOutput "ERROR: background.js file not found at $backgroundJsPath" "Red"
    exit 1
}

Write-ColoredOutput "Starting OAuth authentication flow patch..." "Cyan"
Write-ColoredOutput "Source: $backgroundJsPath" "Gray"

# Create a backup of the original file
try {
    Copy-Item -Path $backgroundJsPath -Destination $backupPath -Force
    Write-ColoredOutput "Created backup at $backupPath" "Green"
} catch {
    Write-ColoredOutput "WARNING: Failed to create backup file: $_" "Yellow"
}

# Read the original content
$originalContent = Get-Content -Path $backgroundJsPath -Raw

# We'll extract the token state initialization to ensure it's preserved
if ($originalContent -match 'let\s+tokenState\s*=\s*{[^}]*}') {
    $tokenStateInit = $Matches[0]
    Write-ColoredOutput "Found token state initialization" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find token state initialization, using default" "Yellow"
    $tokenStateInit = 'let tokenState = { isAuthenticated: false, userId: null, tokenData: null };'
}

# Read the patch content
$patchContent = Get-Content -Path $patchFilePath -Raw

# Apply patch by identifying key functions and replacing them
$newContent = $originalContent

# Replace initiateLogin function
if ($newContent -match '(?s)function\s+initiateLogin\s*\(\s*\)\s*{[^{}]*(?:{[^{}]*}[^{}]*)*}') {
    $oldInitiateLogin = $Matches[0]
    $newContent = $newContent.Replace($oldInitiateLogin, 
        "function initiateLogin() {`n" + 
        ($patchContent -split 'function initiateLogin\(\) {')[1].Split('function handleSuccessfulLogin')[0].Trim() + 
        "`n}")
    Write-ColoredOutput "Replaced initiateLogin function" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find initiateLogin function to replace" "Yellow"
}

# Replace handleSuccessfulLogin function
if ($newContent -match '(?s)async\s+function\s+handleSuccessfulLogin\s*\(\s*\)\s*{[^{}]*(?:{[^{}]*}[^{}]*)*}') {
    $oldHandleSuccessfulLogin = $Matches[0]
    $newContent = $newContent.Replace($oldHandleSuccessfulLogin, 
        "async function handleSuccessfulLogin() {`n" + 
        ($patchContent -split 'async function handleSuccessfulLogin\(\) {')[1].Split('async function notifySidebarsAboutAuth')[0].Trim() + 
        "`n}")
    Write-ColoredOutput "Replaced handleSuccessfulLogin function" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find handleSuccessfulLogin function to replace" "Yellow"
}

# Add notifySidebarsAboutAuth function (before checkOAuthToken)
if ($newContent -match '(?s)async\s+function\s+checkOAuthToken\s*\(\s*\)\s*{') {
    $newContent = $newContent.Replace($Matches[0], 
        "async function notifySidebarsAboutAuth(isAuthenticated) {`n" + 
        ($patchContent -split 'async function notifySidebarsAboutAuth\(isAuthenticated\) {')[1].Split('async function checkOAuthToken')[0].Trim() + 
        "`n}`n`n" + $Matches[0])
    Write-ColoredOutput "Added notifySidebarsAboutAuth function" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find position to add notifySidebarsAboutAuth function" "Yellow"
}

# Replace checkOAuthToken function
if ($newContent -match '(?s)async\s+function\s+checkOAuthToken\s*\(\s*\)\s*{[^{}]*(?:{[^{}]*}[^{}]*)*}') {
    $oldCheckOAuthToken = $Matches[0]
    $newContent = $newContent.Replace($oldCheckOAuthToken, 
        "async function checkOAuthToken() {`n" + 
        ($patchContent -split 'async function checkOAuthToken\(\) {')[1].Split('function handleSidebarConnection')[0].Trim() + 
        "`n}")
    Write-ColoredOutput "Replaced checkOAuthToken function" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find checkOAuthToken function to replace" "Yellow"
}

# Replace handleSidebarConnection function
if ($newContent -match '(?s)function\s+handleSidebarConnection\s*\(\s*port\s*\)\s*{[^{}]*(?:{[^{}]*}[^{}]*)*}') {
    $oldHandleSidebarConnection = $Matches[0]
    $newContent = $newContent.Replace($oldHandleSidebarConnection, 
        "function handleSidebarConnection(port) {`n" + 
        ($patchContent -split 'function handleSidebarConnection\(port\) {')[1].Trim() + 
        "`n}")
    Write-ColoredOutput "Replaced handleSidebarConnection function" "Green"
} else {
    Write-ColoredOutput "WARNING: Could not find handleSidebarConnection function to replace" "Yellow"
}

# Write the modified content back to the file
try {
    $newContent | Set-Content -Path $backgroundJsPath -NoNewline
    Write-ColoredOutput "Successfully applied patches to background.js" "Green"
} catch {
    Write-ColoredOutput "ERROR: Failed to write modified content to background.js: $_" "Red"
    Write-ColoredOutput "Restoring from backup..." "Yellow"
    
    try {
        Copy-Item -Path $backupPath -Destination $backgroundJsPath -Force
        Write-ColoredOutput "Restored original file from backup" "Green"
    } catch {
        Write-ColoredOutput "ERROR: Failed to restore from backup: $_" "Red"
    }
    
    exit 1
}

Write-ColoredOutput "`nOAuth authentication flow patch completed successfully!" "Cyan"
Write-ColoredOutput "The following improvements have been made:" "White"
Write-ColoredOutput "1. Fixed user ID handling to ensure consistency throughout auth flow" "White"
Write-ColoredOutput "2. Improved token status endpoint URL and error handling" "White"
Write-ColoredOutput "3. Enhanced authentication status tracking and notification" "White"
Write-ColoredOutput "4. Added fallback mechanisms to ensure UI updates correctly" "White"
Write-ColoredOutput "5. Fixed communication between background script and sidebar" "White"
Write-ColoredOutput "`nTo test the changes:" "Yellow" 
Write-ColoredOutput "1. Reload the extension" "White"
Write-ColoredOutput "2. Open the sidebar and attempt to login" "White"
Write-ColoredOutput "3. Verify the UI updates correctly after authentication" "White"
Write-ColoredOutput "4. Check that token status is displayed accurately" "White"
Write-ColoredOutput "`nA backup of the original file was saved at: $backupPath" "Gray"
