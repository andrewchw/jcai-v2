# Apply Token Service Fix
# This script enhances the OAuth token service to prevent multiple token refresh services

# Set the working directory to ensure we're in the right place
Set-Location -Path $PSScriptRoot

# Get the full path to the OAuth token service file
$tokenServicePath = Join-Path -Path $PSScriptRoot -ChildPath "app\services\oauth_token_service.py"

# Check if file exists
if (-not (Test-Path $tokenServicePath)) {
    Write-Host "Error: Could not find OAuth token service at $tokenServicePath" -ForegroundColor Red
    Exit 1
}

# Read the file content
$content = Get-Content -Path $tokenServicePath -Raw

# Check if our fix is already applied
if ($content -match "_refresh_thread_running") {
    Write-Host "Token service already has the fix applied" -ForegroundColor Green
    Exit 0
}

# Check if the class already has a _refresh_thread member variable
if (-not ($content -match "\s+self\._refresh_thread\s*=\s*None")) {
    Write-Host "Could not find _refresh_thread initialization in OAuthTokenService" -ForegroundColor Red
    Exit 1
}

# Add class variable after class definition
$content = $content -replace "class OAuthTokenService:", @"
class OAuthTokenService:
    # Class-level flag to track if any refresh thread is running
    _refresh_thread_running = False
"@

# Enhance the start method with thread state tracking
$content = $content -replace "def start\(self\):", @"
def start(self):
        # Class-level check to prevent multiple instances across different objects
        if OAuthTokenService._refresh_thread_running:
            logger.warning("Another OAuth token refresh service is already running")
            return
"@

# Add thread flag setting when thread is started
$content = $content -replace "self\._refresh_thread\.start\(\)", @"
self._refresh_thread.start()
        # Set the running flag
        OAuthTokenService._refresh_thread_running = True
"@

# Add thread flag clearing in the stop method
$content = $content -replace "def stop\(self\):", @"
def stop(self):
        # Reset the class-level running flag when stopping
        OAuthTokenService._refresh_thread_running = False
"@

# Add thread flag clearing at the end of the background refresh loop
$content = $content -replace "def _background_refresh_loop\(self\):", @"
def _background_refresh_loop(self):
        # We'll make sure to reset the running flag when this method exits
        try:
"@

$content = $content -replace "logger\.info\(\"Background refresh loop ended\"\)", @"
logger.info("Background refresh loop ended")
            # Reset the class-level running flag
            OAuthTokenService._refresh_thread_running = False
"@

# Write the modified content back to the file
Set-Content -Path $tokenServicePath -Value $content

Write-Host "Successfully applied token service fix!" -ForegroundColor Green
Write-Host "The OAuth token service now has protection against multiple refresh threads."

# Restart the server to apply the changes
Write-Host ""
Write-Host "To apply these changes, you should restart the server"
Write-Host "You can do this by running: ./restart_server.ps1"
