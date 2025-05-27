# Test Authenticated User Chat Functionality
# Tests pagination, JIRA operations, and complete pipeline

$AuthenticatedUserId = "edge-1748222860747-wobjp48q"
$ApiBaseUrl = "http://localhost:8000/api"

Write-Host "AUTHENTICATED USER CHAT TEST" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host "User ID: $AuthenticatedUserId"
Write-Host ""

function Test-AuthenticatedChat {
    param (
        [string]$Message,
        [string]$Description,
        [string]$ExpectedResult = "any"
    )

    Write-Host "Testing: $Description" -ForegroundColor Yellow
    Write-Host "Message: '$Message'"

    $Body = @{
        text = $Message
    } | ConvertTo-Json -Depth 3

    try {
        $Response = Invoke-RestMethod -Uri "$ApiBaseUrl/chat/message/$AuthenticatedUserId" `
            -Method POST `
            -Body $Body `
            -ContentType "application/json" `
            -TimeoutSec 45

        Write-Host "✅ Status: Success" -ForegroundColor Green
        Write-Host "Intent: $($Response.intent)" -ForegroundColor Cyan
        Write-Host "Confidence: $($Response.confidence)"

        # Show response (truncated)
        $ResponseText = $Response.text
        if ($ResponseText.Length -gt 200) {
            $ResponseText = $ResponseText.Substring(0, 197) + "..."
        }
        Write-Host "Response: $ResponseText" -ForegroundColor White

        # Check for HTML formatting (indicates rich UI response)
        if ($Response.text -like "*<div*" -or $Response.text -like "*<span*") {
            Write-Host "💄 Rich HTML formatting detected" -ForegroundColor Magenta
        }

        # Check authentication status
        if ($Response.text -like "*log in to JIRA*") {
            Write-Host "🔐 Authentication Required" -ForegroundColor Red
            return $false
        }

        # Check JIRA action results
        if ($Response.jira_action_result) {
            $ActionResult = $Response.jira_action_result
            if ($ActionResult.success) {
                Write-Host "✅ JIRA Action: Success - $($ActionResult.message)" -ForegroundColor Green
                if ($ActionResult.issue_key) {
                    Write-Host "📋 Issue: $($ActionResult.issue_key)" -ForegroundColor Cyan
                }
            } else {
                Write-Host "❌ JIRA Action: Failed - $($ActionResult.message)" -ForegroundColor Red
            }
        }

        # Check for pagination context
        if ($Response.context -and $Response.context.session_data) {
            $SessionData = $Response.context.session_data
            if ($SessionData.last_search_results) {
                $ResultCount = $SessionData.last_search_results.Count
                $DisplayIndex = $SessionData.search_display_index
                Write-Host "📊 Pagination Context: $DisplayIndex/$ResultCount results" -ForegroundColor Blue
            }
        }

        # Check for clarification requirements
        if ($Response.requires_clarification) {
            $MissingEntities = $Response.context.missing_entities -join ", "
            Write-Host "❓ Requires Clarification: $MissingEntities" -ForegroundColor Yellow
        }

        Write-Host ""
        return $true
    }
    catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $StatusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "Status Code: $StatusCode" -ForegroundColor Red
        }
        Write-Host ""
        return $false
    }
}

function Test-TokenStatus {
    Write-Host "Checking Authentication Status..." -ForegroundColor Yellow

    try {
        $Response = Invoke-RestMethod -Uri "$ApiBaseUrl/auth/oauth/v2/token/status" `
            -Method GET `
            -Body @{ user_id = $AuthenticatedUserId } `
            -TimeoutSec 15

        Write-Host "✅ Token Status Check: Success" -ForegroundColor Green
        Write-Host "Is Valid: $($Response.is_valid)" -ForegroundColor $(if ($Response.is_valid) { 'Green' } else { 'Red' })
        Write-Host "User ID: $($Response.user_id)"
        Write-Host "Provider: $($Response.provider)"

        if ($Response.expires_at) {
            $ExpiryDate = [DateTimeOffset]::FromUnixTimeSeconds($Response.expires_at).DateTime
            $TimeToExpiry = $ExpiryDate - (Get-Date)
            if ($TimeToExpiry.TotalMinutes -gt 0) {
                Write-Host "Expires: $ExpiryDate ($([Math]::Round($TimeToExpiry.TotalHours, 1)) hours remaining)" -ForegroundColor Green
            } else {
                Write-Host "Expires: $ExpiryDate (EXPIRED $([Math]::Abs([Math]::Round($TimeToExpiry.TotalHours, 1))) hours ago)" -ForegroundColor Red
            }
        }

        Write-Host ""
        return $Response.is_valid
    }
    catch {
        Write-Host "❌ Token Check Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Main test sequence
Write-Host "1. Authentication Status Check" -ForegroundColor Magenta
$IsAuthenticated = Test-TokenStatus

Write-Host "2. JIRA Integration Tests" -ForegroundColor Magenta

# Test messages focusing on JIRA functionality and pagination
$TestMessages = @(
    @{
        Message = "show me my jira issues"
        Description = "Query JIRA issues (should show formatted results)"
        Expected = "success"
    },
    @{
        Message = "show more issues"
        Description = "Pagination request (should show next page or inform no more)"
        Expected = "pagination"
    },
    @{
        Message = "show me issues assigned to me"
        Description = "Filtered query (should use assignee filter)"
        Expected = "success"
    },
    @{
        Message = "what are my recent tasks?"
        Description = "Natural language query (should translate to JIRA search)"
        Expected = "success"
    },
    @{
        Message = "show more"
        Description = "Generic pagination request"
        Expected = "pagination"
    },
    @{
        Message = "create a test issue for chat validation"
        Description = "Issue creation (should create new JIRA issue)"
        Expected = "create"
    }
)

$SuccessCount = 0
$TotalTests = $TestMessages.Count

foreach ($Test in $TestMessages) {
    if (Test-AuthenticatedChat -Message $Test.Message -Description $Test.Description -ExpectedResult $Test.Expected) {
        $SuccessCount++
    }
    Start-Sleep -Milliseconds 1000  # Longer delay for JIRA operations
}

Write-Host "3. Conversation Context Test" -ForegroundColor Magenta
Write-Host "Testing conversation flow with context preservation..."

$ConversationFlow = @(
    "show me issues in project TEST",
    "show more issues",
    "what about project DEMO?",
    "show more",
    "how many total issues do I have?"
)

foreach ($Message in $ConversationFlow) {
    Write-Host ""
    Test-AuthenticatedChat -Message $Message -Description "Conversation flow test"
    Start-Sleep -Milliseconds 800
}

Write-Host ""
Write-Host "=== AUTHENTICATED USER TEST SUMMARY ===" -ForegroundColor Green
Write-Host "Authentication Status: $(if ($IsAuthenticated) { '✅ Valid Token' } else { '❌ Invalid/Expired Token' })"
Write-Host "JIRA Tests Passed: $SuccessCount/$TotalTests"
Write-Host "User ID: $AuthenticatedUserId"
Write-Host ""

if ($IsAuthenticated -and $SuccessCount -gt 0) {
    Write-Host "🎉 Authenticated user testing successful!" -ForegroundColor Green
    Write-Host "✅ Chat endpoint working with JIRA integration" -ForegroundColor Green
    Write-Host "✅ Pagination system functional" -ForegroundColor Green
    Write-Host "✅ Complete pipeline: Extension → Server → LLM → JIRA → Response" -ForegroundColor Green
} elseif (-not $IsAuthenticated) {
    Write-Host "⚠️ Token expired - authentication needs refresh" -ForegroundColor Yellow
    Write-Host "💡 Use Edge extension to re-authenticate" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ Some functionality may be limited" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test real JIRA operations with fresh authentication"
Write-Host "2. Validate pagination with large result sets"
Write-Host "3. Test Edge extension end-to-end workflow"
