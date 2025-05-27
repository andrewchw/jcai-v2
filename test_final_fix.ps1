# Test the final issue creation fix
$headers = @{ 'Content-Type' = 'application/json' }
$body = @{
    text = 'create issue with summary "Test parameter fix" description "Testing the components parameter fix" project "JCAI"'
} | ConvertTo-Json

Write-Host 'Testing issue creation after parameter fix and encryption key setup...'
Write-Host 'User: edge-1748270783635-lun5ucqg'
Write-Host 'Request:' $body
Write-Host ''

try {
    $response = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/message/edge-1748270783635-lun5ucqg' -Method POST -Headers $headers -Body $body
    Write-Host 'SUCCESS: Issue creation test completed'
    Write-Host 'Response:'
    Write-Host ($response | ConvertTo-Json -Depth 5)
} catch {
    Write-Host 'ERROR:' $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host 'Response:' $reader.ReadToEnd()
    }
}
