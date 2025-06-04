# PowerShell script to fix logout functionality
# This script applies both server-side and client-side fixes

param(
    [switch]$ServerOnly,
    [switch]$ClientOnly,
    [string]$ExtensionPath = "..\edge-extension",
    [string]$ServerPath = "."
)

function Apply-ServerFix {
    param (
        [string]$ServerPath
    )

    $oauthMultiPath = Join-Path $ServerPath "app\api\endpoints\oauth_multi.py"

    if (-not (Test-Path $oauthMultiPath)) {
        Write-Error "Cannot find oauth_multi.py at $oauthMultiPath"
        return $false
    }

    Write-Host "Found oauth_multi.py at $oauthMultiPath"
    $content = Get-Content $oauthMultiPath -Raw

    # Check if POST endpoint already exists
    if ($content -match "@router\.post\(`"\/logout`"\)") {
        Write-Host "POST logout endpoint already exists. No server-side changes needed."
        return $true
    }

    # Find the GET logout endpoint
    if (-not ($content -match "@router\.get\(`"\/logout`"\)")) {
        Write-Error "Could not find the GET logout endpoint in oauth_multi.py"
        return $false
    }

    Write-Host "Found GET logout endpoint, preparing to add POST endpoint..."

    # Create the POST endpoint code to insert
    $postEndpointCode = @"

@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Logout and invalidate OAuth token for a user via POST request"""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
"@

    # Use a more direct approach - find the line with GET endpoint and add POST endpoint right after
    $lines = Get-Content $oauthMultiPath
    $modifiedLines = @()
    $foundGetEndpoint = $false
    $skipCount = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $modifiedLines += $lines[$i]

        # When we hit the end of the GET logout function (closing brace),
        # append our new POST endpoint
        if (-not $foundGetEndpoint -and $lines[$i] -match "@router\.get\(`"\/logout`"\)") {
            $foundGetEndpoint = $true
        }

        if ($foundGetEndpoint -and $lines[$i] -match "\s*}\s*$") {
            Write-Host "Found end of GET logout function at line $($i+1)"
            $modifiedLines += ""  # Add a blank line
            $modifiedLines += $postEndpointCode.Split("`n")
            $foundGetEndpoint = $false  # Reset so we don't add it again
        }
    }

    if ($modifiedLines.Count -ne $lines.Count) {
        # Backup the original file
        $backupPath = "$oauthMultiPath.bak"
        Copy-Item $oauthMultiPath $backupPath
        Write-Host "Backed up original file to $backupPath"

        # Write the modified content
        Set-Content -Path $oauthMultiPath -Value $modifiedLines
        Write-Host "Added POST endpoint to oauth_multi.py"
        return $true
    }
    else {
        Write-Error "Failed to modify the file - couldn't find the right location to insert POST endpoint"
        return $false
    }
}

function Create-BackgroundFix {
    param (
        [string]$ExtensionPath
    )

    $backgroundFixPath = Join-Path $ExtensionPath "background_fix.js"

    # Check if file already exists
    if (Test-Path $backgroundFixPath) {
        Write-Host "background_fix.js already exists at $backgroundFixPath"
    }
    else {
        # Create the file with the stopTokenChecking function
        $stopTokenCheckingFunction = @"
/**
 * Stop periodic token checking
 */
function stopTokenChecking() {
    console.log('Stopping periodic token checking');
    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
        self.tokenCheckIntervalId = null;
    }
}
"@

        # Create directory if it doesn't exist
        $extensionDir = [System.IO.Path]::GetDirectoryName($backgroundFixPath)
        if (-not (Test-Path $extensionDir)) {
            New-Item -ItemType Directory -Path $extensionDir -Force | Out-Null
            Write-Host "Created directory: $extensionDir"
        }

        # Write the function to the file
        Set-Content -Path $backgroundFixPath -Value $stopTokenCheckingFunction
        Write-Host "Created background_fix.js at $backgroundFixPath"
    }

    return $true
}

# Main execution
Write-Host "Starting JIRA Chatbot Extension Logout Fix..."

# Apply server-side fix if not explicitly skipped
if (-not $ClientOnly) {
    Write-Host "`nApplying server-side fix..."
    $serverResult = Apply-ServerFix -ServerPath $ServerPath

    if ($serverResult) {
        Write-Host "Server-side fix applied successfully!" -ForegroundColor Green
        Write-Host "You need to restart your FastAPI server for the changes to take effect."
    }
    else {
        Write-Host "Failed to apply server-side fix." -ForegroundColor Red

        # Alternative manual instructions
        Write-Host "`nManual instructions to fix the server:" -ForegroundColor Yellow
        Write-Host "1. Open: app\api\endpoints\oauth_multi.py"
        Write-Host "2. Find the GET logout endpoint (@router.get('/logout'))"
        Write-Host "3. After that function's closing brace, add this code:"
        Write-Host "   ```python"
        Write-Host "   @router.post('/logout')"
        Write-Host "   async def logout_post("
        Write-Host "       user_id: str,"
        Write-Host "       db: Session = Depends(get_db)"
        Write-Host "   ):"
        Write-Host "       '''Logout and invalidate OAuth token for a user via POST request'''"
        Write-Host "       # This simply calls the same implementation as the GET endpoint"
        Write-Host "       return await logout(user_id=user_id, db=db)"
        Write-Host "   ```"
    }
}

# Apply client-side fix if not explicitly skipped
if (-not $ServerOnly) {
    Write-Host "`nApplying client-side fix..."
    $clientResult = Create-BackgroundFix -ExtensionPath $ExtensionPath

    if ($clientResult) {
        Write-Host "Client-side fix prepared successfully!" -ForegroundColor Green
        Write-Host "You need to add the stopTokenChecking function to your background.js file."
        Write-Host "Check the generated file: background_fix.js"
        Write-Host "Add this function before the performLogout function in your extension's background.js file."
    }
}

Write-Host "`nAlternatively, you can modify the browser extension to use GET instead of POST:" -ForegroundColor Yellow
Write-Host "In background.js, find the fetch call in performLogout() and change method: 'POST' to method: 'GET'"

Write-Host "`nFor detailed instructions, run: python fix_logout_functionality.py"
