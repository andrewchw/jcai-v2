$installerPath = "$env:TEMP\nodejs-upgrade\nodejs_installer.msi"

if (Test-Path $installerPath) {
    Write-Host "Node.js installer found. Starting installation..."
    Start-Process msiexec.exe -ArgumentList "/i `"$installerPath`" /quiet" -Verb RunAs -Wait
    Write-Host "Installation completed. Please restart your terminal."
} else {
    Write-Host "Node.js installer not found. Downloading..."
    New-Item -ItemType Directory -Force -Path "$env:TEMP\nodejs-upgrade" | Out-Null
    $url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    Invoke-WebRequest -Uri $url -OutFile $installerPath
    Write-Host "Download completed. Starting installation..."
    Start-Process msiexec.exe -ArgumentList "/i `"$installerPath`" /quiet" -Verb RunAs -Wait
    Write-Host "Installation completed. Please restart your terminal."
}

# Let's verify the installation
Write-Host "Waiting for installation to complete..."
Start-Sleep -Seconds 10
Write-Host "Checking Node.js version..."
try {
    $nodeVersion = & node -v
    Write-Host "Node.js version: $nodeVersion"
} catch {
    Write-Host "Failed to get Node.js version. Please restart your terminal and try again."
}

try {
    $npmVersion = & npm -v
    Write-Host "npm version: $npmVersion"
} catch {
    Write-Host "Failed to get npm version. Please restart your terminal and try again."
}
