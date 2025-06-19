# JCAI Source Code Diagnostic Script
Write-Host "🔍 JCAI Source Code Diagnostic Check" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$ErrorCount = 0
$WarningCount = 0

function Test-JsonFile {
    param($FilePath, $Description)

    Write-Host "`n📋 Testing $Description..." -ForegroundColor Yellow

    if (Test-Path $FilePath) {
        try {
            $content = Get-Content $FilePath -Raw
            $json = ConvertFrom-Json $content
            Write-Host "   ✅ $Description is valid JSON" -ForegroundColor Green
        }
        catch {
            Write-Host "   ❌ $Description has JSON syntax error: $($_.Exception.Message)" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    else {
        Write-Host "   ⚠️ $Description not found at: $FilePath" -ForegroundColor Yellow
        $script:WarningCount++
    }
}

function Test-FileExists {
    param($FilePath, $Description)

    if (Test-Path $FilePath) {
        Write-Host "   ✅ $Description exists" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ $Description missing: $FilePath" -ForegroundColor Red
        $script:ErrorCount++
    }
}

function Test-PythonSyntax {
    param($FilePath, $Description)

    Write-Host "`n🐍 Testing $Description..." -ForegroundColor Yellow

    if (Test-Path $FilePath) {
        try {
            $result = python -m py_compile $FilePath 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ $Description syntax is valid" -ForegroundColor Green
            }
            else {
                Write-Host "   ❌ $Description has syntax errors:" -ForegroundColor Red
                Write-Host "   $result" -ForegroundColor Red
                $script:ErrorCount++
            }
        }
        catch {
            Write-Host "   ⚠️ Cannot test $Description (Python not available)" -ForegroundColor Yellow
            $script:WarningCount++
        }
    }
    else {
        Write-Host "   ❌ $Description not found: $FilePath" -ForegroundColor Red
        $script:ErrorCount++
    }
}

# Test Extension Files
Write-Host "`n🧩 EXTENSION FILES:" -ForegroundColor Cyan

Test-JsonFile "edge-extension\src\manifest.json" "Extension Manifest"

$extensionFiles = @(
    @{Path = "edge-extension\src\js\background.js"; Desc = "Background Script" },
    @{Path = "edge-extension\src\js\content-enhanced.js"; Desc = "Content Script" },
    @{Path = "edge-extension\src\js\jcai-notifications.js"; Desc = "Notification System" },
    @{Path = "edge-extension\src\js\background-notification-integration.js"; Desc = "Background Integration" },
    @{Path = "edge-extension\src\html\sidebar.html"; Desc = "Side Panel HTML" }
)

foreach ($file in $extensionFiles) {
    Test-FileExists $file.Path $file.Desc
}

# Test Python Server Files
Write-Host "`n🐍 PYTHON SERVER FILES:" -ForegroundColor Cyan

$pythonFiles = @(
    @{Path = "python-server\app\main.py"; Desc = "Main Server" },
    @{Path = "python-server\app\services\notification_service.py"; Desc = "Notification Service" },
    @{Path = "python-server\app\services\jira_service.py"; Desc = "JIRA Service" },
    @{Path = "python-server\app\api\endpoints\notifications.py"; Desc = "Notification API" }
)

foreach ($file in $pythonFiles) {
    Test-PythonSyntax $file.Path $file.Desc
}

# Test HTML Files
Write-Host "`n📄 TEST HTML FILES:" -ForegroundColor Cyan

$htmlFiles = @(
    "edge-extension\test-extension-notifications.html",
    "edge-extension\simple-bridge-test.html",
    "test-browser-notifications-fixed-clean.html",
    "basic-js-test.html"
)

foreach ($file in $htmlFiles) {
    Test-FileExists $file "HTML Test File"
}

# Check for common issues
Write-Host "`n🔍 COMMON ISSUE CHECKS:" -ForegroundColor Cyan

# Check if Python server can be imported
Write-Host "`n🐍 Testing Python imports..." -ForegroundColor Yellow
try {
    $importTest = python -c "
import sys
sys.path.append('python-server')
try:
    from app.main import app
    print('✅ Main app imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'❌ Other error: {e}')
" 2>&1

    Write-Host "   $importTest" -ForegroundColor White
}
catch {
    Write-Host "   ⚠️ Cannot test Python imports" -ForegroundColor Yellow
    $script:WarningCount++
}

# Check extension structure
Write-Host "`n🧩 Extension structure check..." -ForegroundColor Yellow

$requiredDirs = @(
    "edge-extension\src\js",
    "edge-extension\src\html",
    "edge-extension\src\images"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "   ✅ Directory exists: $dir" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ Missing directory: $dir" -ForegroundColor Red
        $script:ErrorCount++
    }
}

# Summary
Write-Host "`n📊 DIAGNOSTIC SUMMARY:" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "🎉 ALL CHECKS PASSED!" -ForegroundColor Green
    Write-Host "No errors or warnings found in the source code." -ForegroundColor Green
}
elseif ($ErrorCount -eq 0) {
    Write-Host "✅ NO CRITICAL ERRORS FOUND" -ForegroundColor Green
    Write-Host "⚠️ Warnings: $WarningCount" -ForegroundColor Yellow
}
else {
    Write-Host "❌ ERRORS FOUND: $ErrorCount" -ForegroundColor Red
    Write-Host "⚠️ Warnings: $WarningCount" -ForegroundColor Yellow
    Write-Host "`nPlease fix the errors above before proceeding." -ForegroundColor Red
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
