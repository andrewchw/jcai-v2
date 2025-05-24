# PowerShell script to fix logout functionality
# This script applies both server-side and client-side fixes

param(
    [switch]$ServerOnly,
    [switch]$ClientOnly,
    [string]$ExtensionPath = "..\edge-extension",
    [string]$ServerPath = "."
)

function Apply-ServerFix {
    $oauthMultiPath = Join-Path $ServerPath "app\api\endpoints\oauth_multi.py"
    
    if (-not (Test-Path $oauthMultiPath)) {
        Write-Error "Cannot find oauth_multi.py at $oauthMultiPath"
        return $false
    }
    
    $content = Get-Content $oauthMultiPath -Raw
    
    # Check if POST endpoint already exists
    if ($content -match "router\.post\(`"\/logout`"\)") {
        Write-Host "POST logout endpoint already exists. No server-side changes needed."
        return $true
    }
      # Find the GET logout endpoint
    $getEndpointPattern = "@router\.get\(`"\/logout`"\)"
    if ($content -match $getEndpointPattern) {
        Write-Host "Found GET logout endpoint, adding POST endpoint..."
        
        # Use a simpler approach to find the end of the function
        # We'll look for the function and all of its contents through the closing brace
        $logoutFunctionPattern = "(?s)$getEndpointPattern.*?async def logout\(.*?\).*?}\s*$"
        $functionMatch = [regex]::Match($content, $logoutFunctionPattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
        
        if (-not $functionMatch.Success) {
            # Try a different approach - get the function from the decorator to the end curly brace
            $logoutFunctionPattern = "(?s)($getEndpointPattern.*?})[\r\n]+"
            $functionMatch = [regex]::Match($content, $logoutFunctionPattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
        }
        
        if ($functionMatch.Success) {
            Write-Host "Successfully found the logout function"
            # The indentation doesn't really matter because we're inserting a fully formatted block
            $indentation = "    "
            
            # Create the new POST endpoint
            $postEndpoint = @"

@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Logout and invalidate OAuth token for a user via POST request"""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
"@
              # Insert the new endpoint after the GET endpoint function
            $pattern = "(?s)($getEndpointPattern.*?})"
            $replacement = "$1`r`n`r`n$postEndpoint"
            $newContent = $content -replace $pattern, $replacement
            
            if ($newContent -ne $content) {
                # Backup the original file
                $backupPath = "$oauthMultiPath.bak"
                Copy-Item $oauthMultiPath $backupPath
                Write-Host "Backed up original file to $backupPath"
                
                # Write the updated content
                Set-Content -Path $oauthMultiPath -Value $newContent
                Write-Host "Added POST endpoint to oauth_multi.py"
                return $true
            }
            else {
                Write-Error "Failed to apply regex pattern to add POST endpoint"
                return $false
            }
        }
        else {
            Write-Error "Could not find the logout function definition"
            return $false
        }
    }
    else {
        Write-Error "Could not find the GET logout endpoint in oauth_multi.py"
        return $false
    }
}

# Execute the script
if (-not $ClientOnly) {
    Write-Host "Applying server-side fix..."
    $serverResult = Apply-ServerFix
    if ($serverResult) {
        Write-Host "Server-side fix applied successfully!" -ForegroundColor Green
        Write-Host "Now you need to restart your FastAPI server for the changes to take effect."
    }
    else {
        Write-Host "Failed to apply server-side fix." -ForegroundColor Red
    }
}

if (-not $ServerOnly) {
    Write-Host "`nFor client-side fix:" -ForegroundColor Yellow
    Write-Host "You need to add the stopTokenChecking function to your background.js file."
    Write-Host "Check the generated file: edge-extension\background_fix.js"
    Write-Host "Add this function before the performLogout function in your extension's background.js."
}

Write-Host "`nAlternatively, you can run fix_logout_functionality.py to see detailed instructions."
