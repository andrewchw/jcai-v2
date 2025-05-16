# Run MCP-Atlassian OAuth Setup
# For Windows PowerShell

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $tcpConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port -and $_.State -eq "Listen" }
    return ($tcpConnections -ne $null)
}

# Check if port 8080 is already in use
if (Test-PortInUse -Port 8080) {
    Write-Host "Error: Port 8080 is already in use. OAuth setup requires port 8080." -ForegroundColor Red
    Write-Host "Please stop any processes using port 8080 before running this script." -ForegroundColor Red
    exit 1
}

# Environment file path
$envFilePath = "c:\Users\Loupor\iCloudDocs\iCloudDrive\Documents\VSCode\jcai-v2\mcp-atlassian.env"
# MCP Atlassian storage path
$mcpAtlassianPath = "c:\Users\Loupor\iCloudDocs\iCloudDrive\Documents\VSCode\jcai-v2\.mcp-atlassian"

Write-Host "Starting MCP-Atlassian OAuth setup..." -ForegroundColor Green
Write-Host "This will open a browser window for authentication. Please follow the instructions." -ForegroundColor Yellow

# Run OAuth setup
docker run --rm -it -p 8080:8080 `
  -v "${mcpAtlassianPath}:/home/app/.mcp-atlassian" `
  --env-file $envFilePath `
  ghcr.io/sooperset/mcp-atlassian:latest --oauth-setup -v

Write-Host "OAuth setup completed. You can now start the MCP-Atlassian server." -ForegroundColor Green
