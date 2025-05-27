# PowerShell script to test JIRA Extension Chat API
# This script tests the complete authentication flow and chat functionality

$ApiBaseUrl = "http://localhost:8000/api"
$TestUserId = "test-$(Get-Date -Format 'yyyyMMdd-HHmmss')-$((New-Guid).ToString().Substring(0,8))"

Write-Host "JIRA Extension Chat API Test" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host "Test User ID: $TestUserId"
Write-Host ""

function Test-ChatEndpoint {
    param (
        [string]$Message,
        [string]$Description
    )

    Write-Host "Testing: $Description" -ForegroundColor Yellow
    Write-Host "Message: '$Message'"

    $Body = @{
        text = $Message
    } | ConvertTo-Json -Depth 3

    try {
        $Response = Invoke-RestMethod -Uri "$ApiBaseUrl/chat/message/$TestUserId" `
            -Method POST `
            -Body $Body `
            -ContentType "application/json" `
            -TimeoutSec 30

        Write-Host "✅ Status: Success" -ForegroundColor Green
        Write-Host "Intent: $($Response.intent)"
        Write-Host "Response: $($Response.text.Substring(0, [Math]::Min(100, $Response.text.Length)))..." -ForegroundColor Cyan

        if ($Response.requires_clarification) {
            Write-Host "💡 Requires clarification: Yes" -ForegroundColor Yellow
        }

        if ($Response.jira_action_result) {
            if ($Response.jira_action_result.success) {
                Write-Host "✅ Jira Action: Success" -ForegroundColor Green
            } else {
                Write-Host "❌ Jira Action: Failed - $($Response.jira_action_result.message)" -ForegroundColor Red
            }
        }

        Write-Host ""
        return $true
    }
    catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $StatusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "Status Code: $StatusCode" -ForegroundColor Red

            # Try to get response body for 422 errors
            if ($StatusCode -eq 422) {
                try {
                    $ErrorStream = $_.Exception.Response.GetResponseStream()
                    $Reader = New-Object System.IO.StreamReader($ErrorStream)
                    $ErrorBody = $Reader.ReadToEnd()
                    Write-Host "Error Details: $ErrorBody" -ForegroundColor Red
                }
                catch {
                    Write-Host "Could not read error details" -ForegroundColor Red
                }
            }
        }
        Write-Host ""
        return $false
    }
}

function Test-AuthStatus {
    Write-Host "Testing: Authentication Status Check" -ForegroundColor Yellow

    try {
        $Response = Invoke-RestMethod -Uri "$ApiBaseUrl/auth/oauth/v2/token/status" `
            -Method GET `
            -Body @{ user_id = $TestUserId } `
            -TimeoutSec 15

        Write-Host "✅ Auth Status Check: Success" -ForegroundColor Green
        Write-Host "Is Valid: $($Response.is_valid)"
        Write-Host "User ID: $($Response.user_id)"
        Write-Host ""
        return $Response.is_valid
    }
    catch {
        Write-Host "❌ Auth Check Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

function Test-ServerHealth {
    Write-Host "Testing: Server Health Check" -ForegroundColor Yellow

    try {
        $Response = Invoke-RestMethod -Uri "$ApiBaseUrl/health" `
            -Method GET `
            -TimeoutSec 10

        Write-Host "✅ Health Check: Success" -ForegroundColor Green
        Write-Host "Status: $($Response.status)"
        Write-Host "Multi-user Support: $($Response.features.multi_user_support)"
        Write-Host ""
        return $true
    }
    catch {
        Write-Host "❌ Health Check Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Test sequence
Write-Host "1. Server Health Check" -ForegroundColor Magenta
$HealthOk = Test-ServerHealth

if (-not $HealthOk) {
    Write-Host "❌ Server appears to be down. Please start the Python server first." -ForegroundColor Red
    exit 1
}

Write-Host "2. Authentication Status Check" -ForegroundColor Magenta
$IsAuthenticated = Test-AuthStatus

Write-Host "3. Chat Endpoint Tests (Unauthenticated User)" -ForegroundColor Magenta

# Test various chat scenarios
$TestMessages = @(
    @{ Message = "Hello, can you help me?"; Description = "Basic greeting (should work)" },
    @{ Message = "show me my jira issues"; Description = "Query issues (should require auth)" },
    @{ Message = "create a task for testing"; Description = "Create issue (should require auth)" },
    @{ Message = "show more issues"; Description = "Pagination request (should require auth)" },
    @{ Message = "what can you do?"; Description = "Help request (should work)" }
)

$SuccessCount = 0
$TotalTests = $TestMessages.Count

foreach ($Test in $TestMessages) {
    if (Test-ChatEndpoint -Message $Test.Message -Description $Test.Description) {
        $SuccessCount++
    }
    Start-Sleep -Milliseconds 500  # Small delay between requests
}

Write-Host "4. Performance Test" -ForegroundColor Magenta
Write-Host "Testing parallel vs sequential authentication calls..."

$SequentialTime = Measure-Command {
    Test-AuthStatus | Out-Null
    Test-ServerHealth | Out-Null
}

$ParallelTime = Measure-Command {
    $Job1 = Start-Job -ScriptBlock {
        param($Url, $UserId)
        Invoke-RestMethod -Uri "$Url/auth/oauth/v2/token/status" -Method GET -Body @{ user_id = $UserId }
    } -ArgumentList $ApiBaseUrl, $TestUserId

    $Job2 = Start-Job -ScriptBlock {
        param($Url)
        Invoke-RestMethod -Uri "$Url/health" -Method GET
    } -ArgumentList $ApiBaseUrl

    Wait-Job $Job1, $Job2 | Out-Null
    Remove-Job $Job1, $Job2
}

$PerformanceImprovement = [Math]::Round((($SequentialTime.TotalMilliseconds - $ParallelTime.TotalMilliseconds) / $SequentialTime.TotalMilliseconds) * 100, 1)

Write-Host "Sequential time: $($SequentialTime.TotalMilliseconds) ms" -ForegroundColor Cyan
Write-Host "Parallel time: $($ParallelTime.TotalMilliseconds) ms" -ForegroundColor Cyan
Write-Host "Performance improvement: $PerformanceImprovement%" -ForegroundColor Green

Write-Host ""
Write-Host "=== TEST SUMMARY ===" -ForegroundColor Green
Write-Host "Chat Tests Passed: $SuccessCount/$TotalTests"
Write-Host "Server Health: $(if ($HealthOk) { '✅ OK' } else { '❌ Failed' })"
Write-Host "Authentication: $(if ($IsAuthenticated) { '✅ Authenticated' } else { '⚠️ Not Authenticated (Expected for test user)' })"
Write-Host "Performance Improvement: $PerformanceImprovement%"
Write-Host ""

if ($SuccessCount -eq $TotalTests -and $HealthOk) {
    Write-Host "🎉 All tests passed! Chat endpoint is working correctly." -ForegroundColor Green
} else {
    Write-Host "⚠️ Some tests failed. Check the output above for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test with an authenticated user by logging in via the Edge extension"
Write-Host "2. Test pagination with real Jira data"
Write-Host "3. Test complete end-to-end workflow"
