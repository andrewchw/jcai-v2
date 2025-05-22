#!/usr/bin/env pwsh
#
# Test script for OAuth authentication flow in Jira Chatbot Edge extension
#

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Get-Item $scriptPath).Parent.FullName

function Write-ColoredOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

function Test-ServerEndpoint {
    param (
        [string]$Endpoint,
        [string]$Description
    )
    
    $url = "http://localhost:8000$Endpoint"
    Write-ColoredOutput "Testing $Description endpoint: $url" "Cyan"
    
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing
        Write-ColoredOutput "  Status: $($response.StatusCode) $($response.StatusDescription)" "Green"
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-ColoredOutput "  Failed with status: $statusCode" "Red"
        return $false
    }
}

Write-ColoredOutput "=================================" "Yellow"
Write-ColoredOutput "OAUTH AUTHENTICATION FLOW TESTER" "Yellow"
Write-ColoredOutput "=================================" "Yellow"
Write-ColoredOutput "This script helps verify that the OAuth authentication flow is working correctly.`n"

# Check if server is running
Write-ColoredOutput "Step 1: Checking if server is running..." "Cyan"
$serverRunning = Test-ServerEndpoint -Endpoint "/api/health" -Description "Server health"

if (-not $serverRunning) {
    Write-ColoredOutput "`nERROR: Server doesn't appear to be running. Please start the server first." "Red"
    Write-ColoredOutput "You can run the server using:" "Gray"
    Write-ColoredOutput "  cd $rootPath" "Gray"
    Write-ColoredOutput "  .\run-server.ps1" "Gray"
    exit 1
}

# Check OAuth endpoints
Write-ColoredOutput "`nStep 2: Checking OAuth endpoints..." "Cyan"
$loginEndpoint = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/login" -Description "OAuth login"
$statusEndpoint = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/token/status" -Description "Token status"

if (-not $loginEndpoint -or -not $statusEndpoint) {
    Write-ColoredOutput "`nWARNING: Some OAuth endpoints are not responding correctly." "Yellow"
    Write-ColoredOutput "This may indicate server configuration issues that could affect authentication." "Yellow"
}

# Manual testing steps
Write-ColoredOutput "`nStep 3: Manual testing steps" "Cyan"
Write-ColoredOutput "To complete the OAuth flow testing, please follow these steps:"

Write-ColoredOutput "`n1. Reload your extension in Edge:" "White"
Write-ColoredOutput "   - Open Edge and navigate to edge://extensions/" "Gray"
Write-ColoredOutput "   - Find your Jira Chatbot extension" "Gray"
Write-ColoredOutput "   - Click the reload button (circular arrow icon)" "Gray"

Write-ColoredOutput "`n2. Open the sidebar and check initial state:" "White"
Write-ColoredOutput "   - Click the extension icon to open the sidebar" "Gray"
Write-ColoredOutput "   - Verify if 'Not authenticated' is displayed (expected if not previously authenticated)" "Gray"

Write-ColoredOutput "`n3. Test authentication flow:" "White"
Write-ColoredOutput "   - Click the 'Login' button" "Gray"
Write-ColoredOutput "   - Complete the Jira authentication process" "Gray"
Write-ColoredOutput "   - After redirection, check if the sidebar shows 'Authenticated'" "Gray"
Write-ColoredOutput "   - Verify that token status shows as 'Valid'" "Gray"

Write-ColoredOutput "`n4. Verify user ID consistency:" "White"
Write-ColoredOutput "   - Open developer tools (F12)" "Gray"
Write-ColoredOutput "   - Check console logs for 'User ID' messages" "Gray"
Write-ColoredOutput "   - Confirm the same user ID is used throughout the process" "Gray"

Write-ColoredOutput "`n5. Test token status check:" "White"
Write-ColoredOutput "   - Click 'Check Token' if available, or reload the sidebar" "Gray"
Write-ColoredOutput "   - Verify the token status remains 'Valid'" "Gray"

Write-ColoredOutput "`n6. Test logout process:" "White"
Write-ColoredOutput "   - Click the 'Logout' button" "Gray"
Write-ColoredOutput "   - Verify the sidebar shows 'Not authenticated'" "Gray"
Write-ColoredOutput "   - Verify the 'Login' button is enabled again" "Gray"

Write-ColoredOutput "`nWere all steps completed successfully? [Y/n]: " "Yellow" -NoNewline
$result = Read-Host

if ($result -eq "" -or $result -eq "y" -or $result -eq "Y") {
    Write-ColoredOutput "`nGreat! The OAuth authentication flow appears to be working correctly." "Green"
} else {
    Write-ColoredOutput "`nThere might still be issues with the OAuth flow. Review the console logs for any errors." "Yellow"
    Write-ColoredOutput "If problems persist, you may need to restore from the backup created during patching." "Yellow"
}

Write-ColoredOutput "`nTesting completed!" "Cyan"
