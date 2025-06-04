#!/usr/bin/env pwsh
<#
.SYNOPSIS
    OAuth Diagnostics and Test Tool for Jira Chatbot Extension
.DESCRIPTION
    This script performs a comprehensive check of the OAuth token status,
    server connectivity, and Edge extension configuration.
#>

# Set execution policy for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Helper functions
function Write-StatusMessage {
    param (
        [string]$Message,
        [string]$Status = "Info",
        [switch]$NoNewline
    )

    $color = switch ($Status) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Info" { "Cyan" }
        default { "White" }
    }

    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $color -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $color
    }
}

function Test-ServerConnection {
    param (
        [string]$Url = "http://localhost:8000"
    )

    Write-StatusMessage "Testing connection to $Url..." -Status "Info" -NoNewline

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-StatusMessage " ✓ Connected!" -Status "Success"
            return $true
        } else {
            Write-StatusMessage " ✗ Server responded with status: $($response.StatusCode)" -Status "Warning"
            return $false
        }
    } catch {
        Write-StatusMessage " ✗ Failed to connect: $_" -Status "Error"
        return $false
    }
}

function Get-OAuthTokenStatus {
    param (
        [string]$Url = "http://localhost:8000/api/auth/oauth/token/status"
    )

    Write-StatusMessage "Checking OAuth token status..." -Status "Info" -NoNewline

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        $tokenData = $response.Content | ConvertFrom-Json

        if ($tokenData.status -eq "active") {
            Write-StatusMessage " ✓ Token is active!" -Status "Success"
            return $tokenData
        } else {
            Write-StatusMessage " ✗ Token status: $($tokenData.status)" -Status "Warning"
            return $tokenData
        }
    } catch {
        Write-StatusMessage " ✗ Failed to check token: $_" -Status "Error"
        return $null
    }
}

function Test-TokenFile {
    param (
        [string]$TokenPath = "python-server/oauth_token.json"
    )

    Write-StatusMessage "Checking token file..." -Status "Info" -NoNewline

    if (Test-Path $TokenPath) {
        try {
            $tokenContent = Get-Content $TokenPath -Raw | ConvertFrom-Json
            $hasAccessToken = [bool]$tokenContent.access_token
            $hasRefreshToken = [bool]$tokenContent.refresh_token
            $hasExpiresAt = [bool]$tokenContent.expires_at

            if ($hasAccessToken -and $hasRefreshToken -and $hasExpiresAt) {
                Write-StatusMessage " ✓ Token file is valid!" -Status "Success"
                return $tokenContent
            } else {
                Write-StatusMessage " ✗ Token file is missing required fields" -Status "Warning"
                return $tokenContent
            }
        } catch {
            Write-StatusMessage " ✗ Token file is not valid JSON: $_" -Status "Error"
            return $null
        }
    } else {
        Write-StatusMessage " ✗ Token file not found" -Status "Error"
        return $null
    }
}

# Main script
Clear-Host
Write-StatusMessage "=== JIRA CHATBOT EXTENSION - OAUTH DIAGNOSTICS ===" -Status "Info"
Write-StatusMessage "Running diagnostics at $(Get-Date)" -Status "Info"
Write-StatusMessage "---------------------------------------------------" -Status "Info"

# Go to project root
Push-Location -Path $PSScriptRoot

# 1. Check if server is running
$serverRunning = Test-ServerConnection

# 2. Check token file
$tokenFile = Test-TokenFile

# 3. Check token API status
if ($serverRunning) {
    $tokenStatus = Get-OAuthTokenStatus
} else {
    Write-StatusMessage "Cannot check token API status because server is not running" -Status "Warning"
    $tokenStatus = $null
}

# 4. Display summary
Write-StatusMessage "`nDIAGNOSTICS SUMMARY:" -Status "Info"
Write-StatusMessage "---------------------------------------------------" -Status "Info"

if ($serverRunning) {
    Write-StatusMessage "Server Status: Running" -Status "Success"
} else {
    Write-StatusMessage "Server Status: Not running" -Status "Error"
    Write-StatusMessage "Solution: Run the server with './restart_server.ps1'" -Status "Info"
}

if ($tokenFile) {
    Write-StatusMessage "Token File: Valid" -Status "Success"
    $expiresAt = [DateTimeOffset]::FromUnixTimeSeconds([double]$tokenFile.expires_at).LocalDateTime
    $now = Get-Date
    $timeRemaining = $expiresAt - $now

    if ($expiresAt -gt $now) {
        Write-StatusMessage "Token Expiration: Valid for $([int]$timeRemaining.TotalMinutes) minutes" -Status "Success"
    } else {
        Write-StatusMessage "Token Expiration: EXPIRED" -Status "Error"
        Write-StatusMessage "Solution: Try logging in again or run the OAuth troubleshooter" -Status "Info"
    }
} else {
    Write-StatusMessage "Token File: Missing or invalid" -Status "Error"
    Write-StatusMessage "Solution: Log in again or create a test token with the OAuth troubleshooter" -Status "Info"
}

if ($tokenStatus) {
    $statusColor = if ($tokenStatus.status -eq "active") { "Success" } else { "Warning" }
    Write-StatusMessage "API Token Status: $($tokenStatus.status)" -Status $statusColor

    if ($tokenStatus.status -ne "active") {
        Write-StatusMessage "Solution: Log in again or refresh token with './python-server/refresh_and_check_token.py'" -Status "Info"
    }

    # Show additional token details
    Write-StatusMessage "`nTOKEN DETAILS:" -Status "Info"
    Write-StatusMessage "---------------------------------------------------" -Status "Info"
    Write-StatusMessage "Expires in: $($tokenStatus.expires_in_formatted)" -Status "Info"
    Write-StatusMessage "Last refresh: $($tokenStatus.last_refresh)" -Status "Info"
    Write-StatusMessage "Next check: $($tokenStatus.next_scheduled_check)" -Status "Info"
    Write-StatusMessage "Refresh attempts: $($tokenStatus.refreshes_attempted)" -Status "Info"
    Write-StatusMessage "Successful refreshes: $($tokenStatus.refreshes_succeeded)" -Status "Info"
    Write-StatusMessage "Failed refreshes: $($tokenStatus.refreshes_failed)" -Status "Info"
}

# 5. Edge extension check
Write-StatusMessage "`nEDGE EXTENSION CONNECTION CHECK:" -Status "Info"
Write-StatusMessage "---------------------------------------------------" -Status "Info"
Write-StatusMessage "Checking if extension can connect to server..." -Status "Info"

# Check extension API file
$apiUrl = (Get-Content -Path "edge-extension/src/js/background.js" -Raw) -match "const API_BASE_URL = '(.+?)'"
if ($Matches -and $Matches.Count -gt 1) {
    $extApiUrl = $Matches[1]
    Write-StatusMessage "Extension API URL: $extApiUrl" -Status "Info"

    # Test connection to extension API URL
    $apiUrlNoPath = $extApiUrl -replace "/api$", ""
    Test-ServerConnection -Url $apiUrlNoPath

    # Check if URL matches current server
    if ($extApiUrl -eq "http://localhost:8000/api") {
        Write-StatusMessage "URL Configuration: Correct" -Status "Success"
    } else {
        Write-StatusMessage "URL Configuration: Mismatch" -Status "Warning"
        Write-StatusMessage "Solution: Update API_BASE_URL in background.js to 'http://localhost:8000/api'" -Status "Info"
    }
} else {
    Write-StatusMessage "Could not find API_BASE_URL in background.js" -Status "Warning"
}

# 6. Provide next steps
Write-StatusMessage "`nRECOMMENDED NEXT STEPS:" -Status "Info"
Write-StatusMessage "---------------------------------------------------" -Status "Info"

if (!$serverRunning) {
    Write-StatusMessage "1. Start the server: ./restart_server.ps1" -Status "Info"
} elseif (!$tokenFile -or ($tokenStatus -and $tokenStatus.status -ne "active")) {
    Write-StatusMessage "1. Get a new token: Click 'Login to Jira' in the extension" -Status "Info"
    Write-StatusMessage "2. Or run the OAuth troubleshooter: ./run_oauth_troubleshooter.ps1" -Status "Info"
} else {
    Write-StatusMessage "✓ Everything looks good! The extension should be able to connect to Jira." -Status "Success"
    Write-StatusMessage "If you're still having issues:" -Status "Info"
    Write-StatusMessage "1. Check browser console for errors (F12 in Edge)" -Status "Info"
    Write-StatusMessage "2. Reload the extension in Edge (edge://extensions)" -Status "Info"
    Write-StatusMessage "3. Try the test page: http://localhost:8000/static/test_oauth_flow.html" -Status "Info"
}

# Restore location
Pop-Location
