# Fix scheduler - re-register with Limited (non-elevated) privileges
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TaskName = "MangaAnime-Notifier"
$ProjectRoot = "D:\MangaAnime-Info-delivery-system"

# Remove existing task
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Existing task removed (if any)"

# Define action, trigger, settings
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$ProjectRoot\scripts\run_notifier.bat`"" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Register with current user (interactive session, no elevation)
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description "Anime/Manga daily notifier - runs at 08:00 daily" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Limited `
    -Force

Write-Host "Task registered successfully"

# Show status
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "NextRunTime: $($info.NextRunTime)"
Write-Host "State: $((Get-ScheduledTask -TaskName $TaskName).State)"
