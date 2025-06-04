$body = @{
    message = "Summary : 'Test summary creation', Assignee : 'Anson Chan', Due Date : 'Friday' for Create Issue"
} | ConvertTo-Json

$headers = @{
    'Content-Type' = 'application/json'
}

try {
    Write-Host "Testing chat endpoint with original problematic input..."
    Write-Host "Input: Summary : 'Test summary creation', Assignee : 'Anson Chan', Due Date : 'Friday' for Create Issue"
    Write-Host ""

    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/test_user" -Method POST -Body $body -Headers $headers

    Write-Host "Response received:"
    $response | ConvertTo-Json -Depth 10

    # Check if the response indicates successful entity extraction
    if ($response.text -like "*Test summary creation*" -and
        $response.text -like "*Anson Chan*" -and
        $response.text -like "*Friday*") {
        Write-Host ""
        Write-Host "✅ SUCCESS: All entities (summary, assignee, due date) were properly extracted!" -ForegroundColor Green
    } elseif ($response.action -and $response.action.parameters) {
        Write-Host ""
        Write-Host "✅ SUCCESS: Action generated with parameters:" -ForegroundColor Green
        $response.action.parameters | ConvertTo-Json
    } else {
        Write-Host ""
        Write-Host "❌ ISSUE: Entities may not have been fully extracted" -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
