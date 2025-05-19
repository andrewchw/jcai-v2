Write-Host "Downloading Node.js installer..."

# Create the temp directory
$tempDir = "$env:USERPROFILE\Downloads\nodejs-upgrade"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Download Node.js installer
$installerPath = "$tempDir\node-v20.11.1-x64.msi"
$url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
Invoke-WebRequest -Uri $url -OutFile $installerPath

Write-Host "Download completed. The Node.js installer has been saved to: $installerPath"
Write-Host "Please run the installer manually by navigating to this location and double-clicking the MSI file."
Write-Host "After installation, restart your VS Code to use the new Node.js version."

# Open the folder containing the installer
Invoke-Item (Split-Path -Parent $installerPath)
