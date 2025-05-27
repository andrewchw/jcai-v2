# Test authenticated user chat functionality
$TestUserId = "edge-1748270783635-lun5ucqg"
$ApiBaseUrl = "http://localhost:8000/api"

Write-Host "=== Testing Authenticated User: $TestUserId ===" -ForegroundColor Green
Write-Host ""

# Test 1: Authentication Status
Write-Host "1. Checking Authentication Status..." -ForegroundColor Yellow
try {
    $AuthResponse = Invoke-RestMethod -Uri "$ApiBaseUrl/auth/oauth/v2/token/status?user_id=$TestUserId" -Method GET
    Write-Host "✅ Authentication Check Success" -ForegroundColor Green
    Write-Host "   Is Valid: $($AuthResponse.is_valid)"
    Write-Host "   User ID: $($AuthResponse.user_id)"
    Write-Host "   Has Token: $($AuthResponse.has_token)"
} catch {
    Write-Host "❌ Authentication Check Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Query Issues
Write-Host "2. Testing JIRA Issues Query..." -ForegroundColor Yellow
$TestMessage = "show me my jira issues"
$Body = @{ text = $TestMessage } | ConvertTo-Json

try {
    $ChatResponse = Invoke-RestMethod -Uri "$ApiBaseUrl/chat/message/$TestUserId" -Method POST -Body $Body -ContentType "application/json"
    Write-Host "✅ Chat Request Success" -ForegroundColor Green
    Write-Host "   Intent: $($ChatResponse.intent)"
    Write-Host "   Confidence: $($ChatResponse.confidence)"
    Write-Host ""
    Write-Host "   Response Text:" -ForegroundColor Cyan
    Write-Host "   $($ChatResponse.text)"
    Write-Host ""

    if ($ChatResponse.jira_action_result) {
        if ($ChatResponse.jira_action_result.success) {
            Write-Host "✅ JIRA Action: Success" -ForegroundColor Green
        } else {
            Write-Host "❌ JIRA Action Failed: $($ChatResponse.jira_action_result.message)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️ No JIRA action was executed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Chat Request Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $StatusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $StatusCode" -ForegroundColor Red
    }
}
Write-Host ""

# Test 3: Create Issue
Write-Host "3. Testing Issue Creation..." -ForegroundColor Yellow
$CreateMessage = "create a task for testing the authenticated user integration"
$CreateBody = @{ text = $CreateMessage } | ConvertTo-Json

try {
    $CreateResponse = Invoke-RestMethod -Uri "$ApiBaseUrl/chat/message/$TestUserId" -Method POST -Body $CreateBody -ContentType "application/json"
    Write-Host "✅ Create Issue Request Success" -ForegroundColor Green
    Write-Host "   Intent: $($CreateResponse.intent)"
    Write-Host "   Response: $($CreateResponse.text.Substring(0, [Math]::Min(150, $CreateResponse.text.Length)))..."

    if ($CreateResponse.jira_action_result) {
        if ($CreateResponse.jira_action_result.success) {
            Write-Host "✅ Issue Created Successfully" -ForegroundColor Green
            if ($CreateResponse.jira_action_result.issue_key) {
                Write-Host "   Issue Key: $($CreateResponse.jira_action_result.issue_key)" -ForegroundColor Cyan
            }
        } else {
            Write-Host "❌ Issue Creation Failed: $($CreateResponse.jira_action_result.message)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "❌ Create Issue Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Pagination Test
Write-Host "4. Testing Pagination..." -ForegroundColor Yellow
$MoreMessage = "show more issues"
$MoreBody = @{ text = $MoreMessage } | ConvertTo-Json

try {
    $MoreResponse = Invoke-RestMethod -Uri "$ApiBaseUrl/chat/message/$TestUserId" -Method POST -Body $MoreBody -ContentType "application/json"
    Write-Host "✅ Pagination Request Success" -ForegroundColor Green
    Write-Host "   Intent: $($MoreResponse.intent)"
    Write-Host "   Response: $($MoreResponse.text.Substring(0, [Math]::Min(150, $MoreResponse.text.Length)))..."

    if ($MoreResponse.jira_action_result) {
        if ($MoreResponse.jira_action_result.success) {
            Write-Host "✅ Pagination Successful" -ForegroundColor Green
        } else {
            Write-Host "❌ Pagination Failed: $($MoreResponse.jira_action_result.message)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "❌ Pagination Request Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Authenticated User Test Complete ===" -ForegroundColor Green
