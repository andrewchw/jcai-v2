# Run MCP-Atlassian Server using Docker Compose
# For Windows PowerShell

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $tcpConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port -and $_.State -eq "Listen" }
    return ($tcpConnections -ne $null)
}

# Check if required ports are already in use
$portsToCheck = @(8080, 9000)
$portInUse = $false

foreach ($port in $portsToCheck) {
    if (Test-PortInUse -Port $port) {
        Write-Host "Warning: Port $port is already in use." -ForegroundColor Yellow
        $portInUse = $true
    }
}

if ($portInUse) {
    Write-Host "Some required ports are already in use. This may cause issues." -ForegroundColor Yellow
    Write-Host "Consider stopping any processes using these ports before continuing." -ForegroundColor Yellow
    Write-Host "Press any key to continue or Ctrl+C to abort..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Ask if user wants to run in SSE mode (for Python server integration)
$useSSE = $true
$response = Read-Host "Run in SSE mode for Python server integration? (Y/n)"
if ($response -eq "n" -or $response -eq "N") {
    $useSSE = $false
}

# Environment file path
$envFilePath = "c:\Users\Loupor\iCloudDocs\iCloudDrive\Documents\VSCode\jcai-v2\mcp-atlassian.env"
# MCP Atlassian storage path
$mcpAtlassianPath = "c:\Users\Loupor\iCloudDocs\iCloudDrive\Documents\VSCode\jcai-v2\.mcp-atlassian"

if ($useSSE) {
    Write-Host "Starting MCP-Atlassian server in SSE mode..." -ForegroundColor Green
    docker run --rm -it -p 8080:8080 -p 9000:9000 `
      -v "${mcpAtlassianPath}:/home/app/.mcp-atlassian" `
      --env-file $envFilePath `
      ghcr.io/sooperset/mcp-atlassian:latest `
      --transport sse --port 9000 -vv
} else {
    Write-Host "Starting MCP-Atlassian server in standard mode..." -ForegroundColor Green
    docker run --rm -it -p 8080:8080 `
      -v "${mcpAtlassianPath}:/home/app/.mcp-atlassian" `
      --env-file $envFilePath `
      ghcr.io/sooperset/mcp-atlassian:latest -vv
}
