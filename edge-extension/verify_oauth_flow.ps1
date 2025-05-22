# Add required .NET assembly for HttpUtility
Add-Type -AssemblyName System.Web

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Get-Item $scriptPath).Parent.FullName

# Generate a test user ID similar to the one in the extension
$testUserId = "test-edge-$(Get-Date -Format 'yyyyMMdd-HHmmss')-$(Get-Random -Minimum 10000 -Maximum 99999)"

function Write-ColoredOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

function Get-UserConfirmation {
    param (
        [string]$Message
    )
    
    Write-ColoredOutput "`n$Message (y/n): " "Cyan" -NoNewline
    $response = Read-Host
    return $response.ToLower() -eq 'y'
}

function Test-ServerEndpoint {
    param (
        [string]$Endpoint,
        [string]$Description,
        [hashtable]$Parameters = @{}
    )
    
    $url = "http://localhost:8000$Endpoint"
    
    # Add query parameters if provided
    if ($Parameters.Count -gt 0) {
        $queryString = [System.Web.HttpUtility]::ParseQueryString([string]::Empty)
        foreach ($key in $Parameters.Keys) {
            $queryString.Add($key, $Parameters[$key])
        }
        $url = "$url`?$queryString"
    }
    
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

# Welcome message
Write-ColoredOutput "`n=====================================" "Yellow"
Write-ColoredOutput "OAUTH FLOW VERIFICATION GUIDE" "Yellow" 
Write-ColoredOutput "=====================================`n" "Yellow"
Write-ColoredOutput "This guide will walk you through testing the OAuth authentication flow in the Edge extension.`n" "White"
Write-ColoredOutput "PREREQUISITES:" "Cyan"
Write-ColoredOutput "1. The Python server should be running" "White"
Write-ColoredOutput "2. The Edge extension should be loaded in developer mode" "White"
Write-ColoredOutput "3. Close all Edge extension sidebar instances before starting`n" "White"

# Check if server is running
Write-ColoredOutput "Step 1: Verifying server is running..." "Magenta"
$serverRunning = Test-ServerEndpoint -Endpoint "/api/health" -Description "Server health"

if (-not $serverRunning) {
    Write-ColoredOutput "`nERROR: Server doesn't appear to be running." "Red"
    Write-ColoredOutput "Please start the server using: python -m app.main" "White"
    Write-ColoredOutput "Try running the script again after starting the server.`n" "White"
    exit 1
}

Write-ColoredOutput "`nStep 2: Checking OAuth endpoints..." "Magenta"
$oauthEndpoint = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/login" -Description "OAuth login" -Parameters @{
    "user_id" = $testUserId
}

if (-not $oauthEndpoint) {
    Write-ColoredOutput "`nWARNING: OAuth login endpoint not available." "Yellow"
    if (-not (Get-UserConfirmation "Continue anyway?")) {
        exit 1
    }
}

Write-ColoredOutput "`nStep 3: Testing token status endpoint..." "Magenta"
Write-ColoredOutput "Using test user ID: $testUserId" "Gray"
$tokenStatusEndpoint = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/token/status" -Description "Token status" -Parameters @{
    "user_id" = $testUserId
}

if (-not $tokenStatusEndpoint) {
    Write-ColoredOutput "`nWARNING: Token status endpoint not available." "Yellow"
    if (-not (Get-UserConfirmation "Continue anyway?")) {
        exit 1
    }
}

# Manual verification steps
Write-ColoredOutput "`nMANUAL VERIFICATION STEPS:" "Cyan"
Write-ColoredOutput "Test user ID: $testUserId (use this if you need to manually check logs)" "Gray"
Write-ColoredOutput "1. Open Edge and navigate to any webpage" "White"
Write-ColoredOutput "2. Click the JIRA Chatbot icon to open the sidebar" "White"
Write-ColoredOutput "3. Go to the Settings tab" "White"
Write-ColoredOutput "4. Check initial authentication status (should be not authenticated)" "White"
Write-ColoredOutput "5. Click the 'Login' button" "White"
Write-ColoredOutput "6. Complete the OAuth flow in the popup window" "White"
Write-ColoredOutput "7. Verify that the UI updates to show 'Authenticated'" "White"
Write-ColoredOutput "8. Check the token status information" "White"
Write-ColoredOutput "9. Close and reopen the sidebar to verify persistence" "White"
Write-ColoredOutput "10. Test logout functionality" "White"

Write-ColoredOutput "`nCHECKLIST:" "Magenta"
Write-ColoredOutput "□ Authentication status updates correctly after login" "White"
Write-ColoredOutput "□ User ID is consistent between requests" "White"
Write-ColoredOutput "□ Token status shows valid information" "White"
Write-ColoredOutput "□ Status persists when reopening sidebar" "White"
Write-ColoredOutput "□ Logout works correctly" "White"
Write-ColoredOutput "□ No errors in browser console about 'window is not defined'" "White"

Write-ColoredOutput "`nAdditional Debugging Tips:" "Cyan"
Write-ColoredOutput "- Check Edge browser console for any errors" "White"
Write-ColoredOutput "- Examine server logs for API request issues" "White"
Write-ColoredOutput "- Use Edge extension debugging: edge://extensions/ > Details > background.html" "White"

Write-ColoredOutput "`nEnd of verification guide. Please report any issues encountered.`n" "Yellow"
