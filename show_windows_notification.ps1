#!/usr/bin/env powershell
# Show Windows Toast Notification (bypasses browser restrictions)

param(
    [string]$Title = "🔔 JCAI Notification",
    [string]$Message = "New issue assigned to you: JCAI-124",
    [string]$AppId = "Microsoft.Windows.Explorer"
)

Write-Host "📱 Showing Windows Toast Notification..." -ForegroundColor Green

try {
    # Import required assemblies for Windows notifications
    Add-Type -AssemblyName System.Windows.Forms

    # Create Windows Toast Notification
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    # Create the toast template
    $Template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)

    # Set the text content
    $RawXml = [xml] $Template.GetXml()
    ($RawXml.toast.visual.binding.text | Where-Object {$_.id -eq "1"}).AppendChild($RawXml.CreateTextNode($Title)) | Out-Null
    ($RawXml.toast.visual.binding.text | Where-Object {$_.id -eq "2"}).AppendChild($RawXml.CreateTextNode($Message)) | Out-Null

    # Load the updated XML
    $SerializedXml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $SerializedXml.LoadXml($RawXml.OuterXml)

    # Create and show the toast
    $Toast = [Windows.UI.Notifications.ToastNotification]::new($SerializedXml)
    $Toast.Tag = "JCAI-Notification"
    $Toast.Group = "JCAI-Group"

    $Notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId)
    $Notifier.Show($Toast)

    Write-Host "✅ Windows notification sent successfully!" -ForegroundColor Green

} catch {
    Write-Host "❌ Windows Toast failed, falling back to balloon notification..." -ForegroundColor Yellow

    try {
        # Fallback: Use System.Windows.Forms balloon notification
        Add-Type -AssemblyName System.Windows.Forms

        $notifyIcon = New-Object System.Windows.Forms.NotifyIcon
        $notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
        $notifyIcon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
        $notifyIcon.BalloonTipText = $Message
        $notifyIcon.BalloonTipTitle = $Title
        $notifyIcon.Visible = $true

        $notifyIcon.ShowBalloonTip(5000)

        # Keep the icon visible for a moment, then clean up
        Start-Sleep -Seconds 6
        $notifyIcon.Dispose()

        Write-Host "✅ Balloon notification sent successfully!" -ForegroundColor Green

    } catch {
        Write-Host "❌ All notification methods failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "💡 Alternative: Browser custom notifications are available in the test page." -ForegroundColor Cyan
    }
}

# Show usage info
Write-Host ""
Write-Host "💡 Usage examples:" -ForegroundColor Cyan
Write-Host "   .\show_windows_notification.ps1" -ForegroundColor White
Write-Host "   .\show_windows_notification.ps1 -Title 'Custom Title' -Message 'Custom message'" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Test the enhanced browser notifications at:" -ForegroundColor Cyan
Write-Host "   http://localhost:3000/test-browser-notifications-enhanced.html" -ForegroundColor White
