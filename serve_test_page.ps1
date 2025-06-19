#!/usr/bin/env powershell
# Serve test page via HTTP to avoid file:// permission issues

Write-Host "🌐 Starting simple HTTP server for notification test page..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Blue

    # Start Python HTTP server on port 3000
    Write-Host "Starting HTTP server on http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""    Write-Host "🔗 Test pages will be available at:" -ForegroundColor Green
    Write-Host "   http://localhost:3000/test-browser-notifications-enhanced.html (RECOMMENDED)" -ForegroundColor Cyan
    Write-Host "   http://localhost:3000/test-browser-notifications.html (Original)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 For Edge permission issues, use the ENHANCED version!" -ForegroundColor Yellow
    Write-Host ""

    # Start server and open enhanced browser test page
    Start-Process "http://localhost:3000/test-browser-notifications-enhanced.html"
    python -m http.server 3000

} catch {
    Write-Host "❌ Python not found. Using PowerShell alternative..." -ForegroundColor Red

    # Alternative: Start simple PowerShell HTTP server
    Write-Host "Starting PowerShell HTTP server on http://localhost:3000" -ForegroundColor Yellow

    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:3000/")
    $listener.Start()
      Write-Host "✅ Server started! Opening enhanced test page..." -ForegroundColor Green
    Start-Process "http://localhost:3000/test-browser-notifications-enhanced.html"

    try {
        while ($listener.IsListening) {
            $context = $listener.GetContext()
            $request = $context.Request
            $response = $context.Response
              $path = $request.Url.AbsolutePath
            if ($path -eq "/test-browser-notifications-enhanced.html" -or $path -eq "/" -or $path -eq "/test-browser-notifications.html") {
                $filePath = if ($path -eq "/test-browser-notifications.html") { "test-browser-notifications.html" } else { "test-browser-notifications-enhanced.html" }
                if (Test-Path $filePath) {
                    $content = Get-Content $filePath -Raw
                    $buffer = [System.Text.Encoding]::UTF8.GetBytes($content)
                    $response.ContentType = "text/html"
                    $response.ContentLength64 = $buffer.Length
                    $response.OutputStream.Write($buffer, 0, $buffer.Length)
                } else {
                    $response.StatusCode = 404
                    $errorMsg = "File not found: $filePath"
                    $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorMsg)
                    $response.OutputStream.Write($buffer, 0, $buffer.Length)
                }
            } else {
                $response.StatusCode = 404
                $errorMsg = "Not found: $path"
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorMsg)
                $response.OutputStream.Write($buffer, 0, $buffer.Length)
            }

            $response.Close()
        }
    } finally {
        $listener.Stop()
    }
}
