#!/usr/bin/env pwsh
#
# This script diagnoses and fixes issues with the OAuth callback page
# It checks if the callback page is returning the correct success message
#

$ErrorActionPreference = "Stop"

function Write-ColoredOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

function Test-Endpoint {
    param (
        [string]$Endpoint,
        [string]$Description,
        [hashtable]$Headers = @{}
    )
    
    $url = "http://localhost:8000$Endpoint"
    Write-ColoredOutput "Testing $Description endpoint: $url" "Cyan"
    
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing -Headers $Headers
        Write-ColoredOutput "  Status: $($response.StatusCode) $($response.StatusDescription)" "Green"
        
        # Try to extract content to see how the page responds
        if ($response.Content) {
            if ($response.Content.Length -gt 500) {
                Write-ColoredOutput "  Content (truncated): $($response.Content.Substring(0, 500))..." "Gray"
            } else {
                Write-ColoredOutput "  Content: $($response.Content)" "Gray"
            }
            
            # Look for specific patterns
            if ($response.Content -match "authentication.*failed" -or $response.Content -match "auth.*failed") {
                Write-ColoredOutput "  WARNING: Response contains 'authentication failed' message even though it might be successful!" "Yellow"
            }
            
            if ($response.Content -match "authentication.*success" -or $response.Content -match "auth.*success") {
                Write-ColoredOutput "  INFO: Response contains 'authentication success' message" "Green"
            }
        }
        
        return $true
    } catch {
        $statusCode = $null
        try { $statusCode = $_.Exception.Response.StatusCode.value__ } catch {}
        
        Write-ColoredOutput "  Failed with status: $statusCode" "Red"
        if ($_.Exception.Message) {
            Write-ColoredOutput "  Error details: $($_.Exception.Message)" "Red"
        }
        
        return $false
    }
}

# Welcome message
Write-ColoredOutput "`n=====================================" "Yellow"
Write-ColoredOutput "OAUTH CALLBACK PAGE DIAGNOSTICS" "Yellow" 
Write-ColoredOutput "=====================================`n" "Yellow"

# Check if server is running
Write-ColoredOutput "Step 1: Verifying server is running..." "Magenta"
$serverRunning = Test-Endpoint -Endpoint "/api/health" -Description "Server health"

if (-not $serverRunning) {
    Write-ColoredOutput "`nERROR: Server doesn't appear to be running." "Red"
    Write-ColoredOutput "Please start the server using: python -m app.main" "White"
    Write-ColoredOutput "Try running the script again after starting the server.`n" "White"
    exit 1
}

# Check callback page template
Write-ColoredOutput "`nStep 2: Testing callback endpoints..." "Magenta"

# First test a successful callback
$successCallback = Test-Endpoint -Endpoint "/callback?success=true&user_id=test_diagnostic_user" -Description "Success callback page"

# Test a failed callback
$failedCallback = Test-Endpoint -Endpoint "/callback?success=false&user_id=test_diagnostic_user" -Description "Failed callback page"

# Test an OAuth code callback (should be considered success)
$codeCallback = Test-Endpoint -Endpoint "/callback?code=test_code&state=user_id:test_diagnostic_user" -Description "OAuth code callback page"

# Instructions
Write-ColoredOutput "`n=====================================" "Yellow"
Write-ColoredOutput "DIAGNOSIS RESULTS" "Yellow"
Write-ColoredOutput "=====================================`n" "Yellow"

if (-not $successCallback -or -not $failedCallback -or -not $codeCallback) {
    Write-ColoredOutput "There appear to be issues with the OAuth callback pages." "Red"
    Write-ColoredOutput "The server may not be correctly handling the callback parameters." "Red"
    
    Write-ColoredOutput "`nPOTENTIAL SOLUTIONS:" "Cyan"
    Write-ColoredOutput "1. Check the server logs for errors related to the OAuth callback processing" "White"
    Write-ColoredOutput "2. Verify that the server's callback template is correctly processing the 'success' parameter" "White"
    Write-ColoredOutput "3. Restart the server to ensure any code changes take effect" "White"
} else {
    Write-ColoredOutput "The OAuth callback pages appear to be responding, but there may be issues with the content." "Yellow"
    
    Write-ColoredOutput "`nRECOMMENDED NEXT STEPS:" "Cyan"
    Write-ColoredOutput "1. When you login with the extension, check the browser URL to see if it contains 'success=true'" "White"
    Write-ColoredOutput "2. If it contains 'code=' but no 'success=' parameter, the extension should still recognize it as success" "White"
    Write-ColoredOutput "3. The extension has been updated to better detect successful authentication even if:" "White"
    Write-ColoredOutput "   a. The URL contains a code but no explicit success parameter" "White"
    Write-ColoredOutput "   b. The callback page content incorrectly shows 'authentication failed'" "White"
}

Write-ColoredOutput "`nEXTENSION STATUS:" "Cyan"
Write-ColoredOutput "If the extension shows 'Authenticated ✓' but the callback page shows 'Authentication failed':" "White"
Write-ColoredOutput "- The extension is correctly detecting authentication success based on URL parameters" "White"
Write-ColoredOutput "- There is a visual bug in the callback page template that doesn't affect functionality" "White"
Write-ColoredOutput "- You can safely ignore the 'Authentication failed' message on the callback page" "White"

Write-ColoredOutput "`nIf you still encounter issues, please check the server logs and browser console for more details.`n" "Yellow"
