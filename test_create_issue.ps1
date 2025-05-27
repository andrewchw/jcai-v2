# Test Create Issue Fix
$headers = @{ 'Content-Type' = 'application/json' }
$body = @{
    text = 'create issue with summary "Test issue creation" description "Testing the fix for create issue method"'
} | ConvertTo-Json

Write-Host 'Testing issue creation with authenticated user edge-1748270783635-lun5ucqg...'
try {
    $response = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/message/edge-1748270783635-lun5ucqg' -Method POST -Headers $headers -Body $body
    Write-Host 'SUCCESS: Issue creation test completed'
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host 'ERROR:' $_.Exception.Message
    if ($_.Exception.Response) {
        $errorContent = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorContent)
        Write-Host 'Response:' $reader.ReadToEnd()
    }
}
