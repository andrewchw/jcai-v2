#!/usr/bin/env pwsh
# Script to diagnose Jira API connection issues in the JCAI server

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Get-Item $scriptPath).Parent.FullName
$serverPath = Join-Path $rootPath "python-server"

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
        [string]$Description,
        [string]$UserId = "test-diagnostic-user",
        [switch]$DetailedOutput = $false
    )
    
    $url = "http://localhost:8000$Endpoint"
    if ($Endpoint -like "*`?*") {
        $url = "${url}&_diagnostic=true"
    } else {
        $url = "${url}?_diagnostic=true"
    }
    
    Write-ColoredOutput "Testing $Description endpoint: $url" "Cyan"
    
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing
        Write-ColoredOutput "  Status: $($response.StatusCode) $($response.StatusDescription)" "Green"
        
        if ($DetailedOutput) {
            try {
                $content = $response.Content
                $jsonData = $content | ConvertFrom-Json
                Write-ColoredOutput "  Response Data:" "White"
                Write-ColoredOutput "$($jsonData | ConvertTo-Json -Depth 3)" "Gray"
            } catch {
                Write-ColoredOutput "  Response: $content" "Gray"
            }
        } else {
            Write-ColoredOutput "  Response: $($response.Content)" "Gray"
        }
        
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorDetails = ""
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $errorDetails = $reader.ReadToEnd()
        } catch {
            $errorDetails = "Could not read error details"
        }
        
        Write-ColoredOutput "  Failed with status: $statusCode" "Red"
        Write-ColoredOutput "  Error details: $errorDetails" "Red"
        return $false
    }
}

# Welcome message
Write-ColoredOutput "`n=====================================" "Yellow"
Write-ColoredOutput "JIRA API CONNECTION DIAGNOSTICS" "Yellow" 
Write-ColoredOutput "=====================================`n" "Yellow"

# Check if server is running
Write-ColoredOutput "Step 1: Verifying server is running..." "Magenta"
$serverRunning = Test-ServerEndpoint -Endpoint "/api/health" -Description "Server health"

if (-not $serverRunning) {
    Write-ColoredOutput "`nERROR: Server doesn't appear to be running." "Red"
    Write-ColoredOutput "Please start the server using: python -m app.main" "White"
    Write-ColoredOutput "Try running the script again after starting the server.`n" "White"
    exit 1
}

# Check OAuth token status
Write-ColoredOutput "`nStep 2: Checking OAuth token status..." "Magenta"
$testUserId = "test-diagnostic-$(Get-Date -Format 'yyyyMMdd-HHmmss')-$(Get-Random -Minimum 10000 -Maximum 99999)"
Write-ColoredOutput "Using test user ID: $testUserId" "Yellow"
$tokenStatus = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/token/status?user_id=$testUserId" -Description "OAuth token status" -DetailedOutput

# Check if there's a valid OAuth token in the system
Write-ColoredOutput "`nStep 3: Checking if server has a valid OAuth token..." "Magenta"
$tokenDebug = Test-ServerEndpoint -Endpoint "/api/auth/oauth/v2/debug" -Description "OAuth token debug" -DetailedOutput

# Check Jira API health specifically
Write-ColoredOutput "`nStep 4: Testing Jira API health..." "Magenta"
$jiraHealth = Test-ServerEndpoint -Endpoint "/api/jira/v2/health" -Description "Jira API health" -UserId $testUserId -DetailedOutput

# Check Jira projects endpoint
Write-ColoredOutput "`nStep 5: Testing Jira projects endpoint..." "Magenta"
$projectsEndpoint = Test-ServerEndpoint -Endpoint "/api/jira/v2/projects?user_id=$testUserId" -Description "Jira projects" -UserId $testUserId -DetailedOutput

# Check Jira issues endpoint
Write-ColoredOutput "`nStep 6: Testing Jira issues endpoint..." "Magenta"
$issuesEndpoint = Test-ServerEndpoint -Endpoint "/api/jira/v2/issues?user_id=$testUserId" -Description "Jira issues" -UserId $testUserId -DetailedOutput

# Output server logs for more context
Write-ColoredOutput "`nStep 7: Checking server logs..." "Magenta"

# Check OAuth debug log
$oauthLogFile = Join-Path $serverPath "oauth_debug.log"
if (Test-Path $oauthLogFile) {
    $logContent = Get-Content -Path $oauthLogFile -Tail 20
    Write-ColoredOutput "Last 20 lines of OAuth debug log:" "White"
    foreach ($line in $logContent) {
        if ($line -match "ERROR") {
            Write-Host $line -ForegroundColor Red
        } else {
            Write-Host $line
        }
    }
} else {
    Write-ColoredOutput "  Could not find OAuth debug log file" "Yellow"
}

# Check OAuth token service log
$tokenLogFile = Join-Path $serverPath "oauth_token_service.log"
if (Test-Path $tokenLogFile) {
    $logContent = Get-Content -Path $tokenLogFile -Tail 10
    Write-ColoredOutput "`nLast 10 lines of OAuth token service log:" "White"
    foreach ($line in $logContent) {
        if ($line -match "ERROR") {
            Write-Host $line -ForegroundColor Red
        } else {
            Write-Host $line
        }
    }
} else {
    Write-ColoredOutput "  Could not find OAuth token service log file" "Yellow"
}

# Check app log if exists
$appLogFile = Join-Path $serverPath "app.log"
if (Test-Path $appLogFile) {
    $logContent = Get-Content -Path $appLogFile -Tail 10
    Write-ColoredOutput "`nLast 10 lines of app log:" "White"
    foreach ($line in $logContent) {
        if ($line -match "ERROR") {
            Write-Host $line -ForegroundColor Red
        } else {
            Write-Host $line
        }
    }
} else {
    Write-ColoredOutput "  Could not find app log file" "Yellow"
}

# Provide diagnosis and recommendations
Write-ColoredOutput "`nDIAGNOSIS:" "Green"

# Analysis of results
$oauthOk = $tokenStatus
$jiraApiOk = $jiraHealth -and $projectsEndpoint -and $issuesEndpoint
$serverOk = $serverRunning

if ($serverOk -and $oauthOk -and $jiraApiOk) {
    Write-ColoredOutput "All systems are functioning correctly! OAuth and Jira API appear to be working." "Green"
} elseif ($serverOk -and $oauthOk -and -not $jiraApiOk) {
    Write-ColoredOutput "OAuth authentication is working, but there's an issue with the Jira API integration." "Yellow"
    Write-ColoredOutput "This is the most common pattern: token status is 200 OK but Jira API calls fail." "Yellow"
    Write-ColoredOutput "`nPossible issues:" "Cyan"
    Write-ColoredOutput "1. The OAuth token doesn't have the correct Jira API permissions" "White"
    Write-ColoredOutput "2. The server's Jira API integration is misconfigured" "White"
    Write-ColoredOutput "3. The connection between the server and Jira API is broken" "White"
    Write-ColoredOutput "4. The authenticated Jira account doesn't have access to projects or issues" "White"
} elseif ($serverOk -and -not $oauthOk) {
    Write-ColoredOutput "There's an issue with the OAuth authentication service." "Red"
    Write-ColoredOutput "`nPossible issues:" "Cyan"
    Write-ColoredOutput "1. OAuth token may be expired or invalid" "White"
    Write-ColoredOutput "2. OAuth service might not be configured correctly" "White"
} else {
    Write-ColoredOutput "Server connection issues detected." "Red"
}

# Recommended actions
Write-ColoredOutput "`nRECOMMENDATIONS:" "Cyan"

if (-not $jiraApiOk) {
    Write-ColoredOutput "To fix Jira API issues:" "White"
    Write-ColoredOutput "1. Run the Jira connection test script to get detailed diagnostics:" "White"
    Write-ColoredOutput "   > cd $serverPath" "Gray"
    Write-ColoredOutput "   > python test_jira_connection.py" "Gray"
    Write-ColoredOutput "2. Check if the Jira API credentials in the server are correct" "White"
    Write-ColoredOutput "3. Verify the OAuth scopes include 'read:jira-user read:jira-work write:jira-work'" "White"
    Write-ColoredOutput "4. Try revoking and regenerating the OAuth token completely" "White"
    Write-ColoredOutput "5. Examine the server logs for additional error details" "White"
}

if (-not $oauthOk) {
    Write-ColoredOutput "`nTo fix OAuth issues:" "White"
    Write-ColoredOutput "1. Run the OAuth troubleshooter to help diagnose the problem:" "White"
    Write-ColoredOutput "   > cd $rootPath" "Gray"
    Write-ColoredOutput "   > python .\run_oauth_troubleshooter.ps1" "Gray"
    Write-ColoredOutput "2. Check the OAuth configuration in the server" "White"
    Write-ColoredOutput "3. Try manually generating a new token" "White"
}

Write-ColoredOutput "`nFor Edge extension users:" "White"
Write-ColoredOutput "1. If you're experiencing 'Invalid token' in the UI while the token status shows valid," "White"
Write-ColoredOutput "   this confirms the issue is with the Jira API integration, not the OAuth token itself." "White"
Write-ColoredOutput "2. The server logs should show 500 errors for Jira API calls despite 200 OK for token status" "White"
Write-ColoredOutput "3. Update your extension to handle this scenario better by showing a more helpful error message" "White"

Write-ColoredOutput "`nEND OF DIAGNOSTIC REPORT" "Yellow"

if (-not $projectsEndpoint -or -not $issuesEndpoint) {
    Write-ColoredOutput "The server is responding to OAuth token requests but failing on Jira API calls." "Yellow"
    Write-ColoredOutput "This indicates a problem with the Jira API connection configuration or permissions." "Yellow"
    
    Write-ColoredOutput "`nRECOMMENDED ACTIONS:" "Green"
    Write-ColoredOutput "1. Check that the Jira API credentials are correctly configured" "White"
    Write-ColoredOutput "2. Verify that the OAuth token has the correct Jira API scopes" "White"
    Write-ColoredOutput "3. Check that the Jira instance is accessible from the server" "White"
    Write-ColoredOutput "4. Review the server logs for specific error messages" "White"
    Write-ColoredOutput "5. Try refreshing the OAuth token or re-authenticating" "White"
} else {
    Write-ColoredOutput "All endpoints are responding correctly. If you're still seeing issues in the extension, check:" "Green"
    Write-ColoredOutput "1. Whether the authenticated user in the extension has the correct permissions" "White"
    Write-ColoredOutput "2. If there are any network connectivity issues between the extension and server" "White"
    Write-ColoredOutput "3. Browser console logs for any JavaScript errors" "White"
}

Write-ColoredOutput "`nEnd of diagnostic report. Please use this information to resolve Jira connection issues.`n" "Yellow"
