# ===========================================================
# MangaAnime-Info-delivery-system Task Scheduler Setup Script
# Registers a daily 08:00 task in Windows Task Scheduler
# ===========================================================

# UTF-8 output setting
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Configuration variables
$TaskName        = "MangaAnime-Notifier"
$TaskDescription = "Anime/Manga info auto-collection with Gmail notification and Google Calendar integration"
$ProjectRoot     = "D:\MangaAnime-Info-delivery-system"
$ScriptPath      = "$ProjectRoot\scripts\run_notifier.bat"
$LogFile         = "$ProjectRoot\logs\scheduler.log"
$TriggerTime     = "08:00"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " MangaAnime-Notifier Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Ensure log directory exists
$LogDir = "$ProjectRoot\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "[INFO] Log directory created: $LogDir" -ForegroundColor Green
}

# Verify BAT file exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "[ERROR] Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}
Write-Host "[INFO] Script verified: $ScriptPath" -ForegroundColor Green

# Remove existing task if present
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "[INFO] Removing existing task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[INFO] Existing task removed" -ForegroundColor Yellow
}

# Action definition: run BAT file via cmd.exe
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

# Trigger definition: daily at 08:00
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $TriggerTime

# Settings definition
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Determine current user
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Write-Host "[INFO] Registering task..." -ForegroundColor Cyan
Write-Host "  Task Name  : $TaskName" -ForegroundColor White
Write-Host "  User       : $CurrentUser" -ForegroundColor White
Write-Host "  Script     : $ScriptPath" -ForegroundColor White
Write-Host "  Schedule   : Daily at $TriggerTime" -ForegroundColor White
Write-Host "  Log File   : $LogFile" -ForegroundColor White
Write-Host ""

# Flag to track registration success
$RegistrationSuccess = $false

# Attempt registration with current user (S4U - no password required)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType S4U `
    -RunLevel Highest

try {
    $RegisteredTask = Register-ScheduledTask `
        -TaskName    $TaskName `
        -Description $TaskDescription `
        -Action      $Action `
        -Trigger     $Trigger `
        -Settings    $Settings `
        -Principal   $Principal `
        -Force

    $RegistrationSuccess = $true
    Write-Host "[SUCCESS] Task registered successfully with current user account" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "[WARN] Registration with current user failed: $_" -ForegroundColor Yellow
}

# Fallback: register with SYSTEM account if previous attempt failed
if (-not $RegistrationSuccess) {
    Write-Host "[INFO] Retrying with SYSTEM account..." -ForegroundColor Yellow

    $FallbackPrincipal = New-ScheduledTaskPrincipal `
        -UserId "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    try {
        $RegisteredTask = Register-ScheduledTask `
            -TaskName    $TaskName `
            -Description $TaskDescription `
            -Action      $Action `
            -Trigger     $Trigger `
            -Settings    $Settings `
            -Principal   $FallbackPrincipal `
            -Force

        $RegistrationSuccess = $true
        Write-Host "[SUCCESS] Task registered successfully with SYSTEM account" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Fallback registration also failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Verify registered task status
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Registered Task Status" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$TaskInfo = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($TaskInfo) {
    Write-Host "Task Name  : $($TaskInfo.TaskName)" -ForegroundColor White
    Write-Host "State      : $($TaskInfo.State)" -ForegroundColor White
    Write-Host "Description: $($TaskInfo.Description)" -ForegroundColor White

    # Display trigger info
    $TaskDetails = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($TaskDetails) {
        $NextRun = $TaskDetails.NextRunTime
        if ($NextRun) {
            Write-Host "Next Run   : $NextRun" -ForegroundColor White
        }
        $LastRun = $TaskDetails.LastRunTime
        $MinTime = [DateTime]::MinValue
        if ($LastRun -and ($LastRun -ne $MinTime)) {
            Write-Host "Last Run   : $LastRun" -ForegroundColor White
            Write-Host "Last Result: $($TaskDetails.LastTaskResult)" -ForegroundColor White
        }
    }
}
else {
    Write-Host "[ERROR] Failed to verify task registration" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Setup Complete" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "[INFO] Logs will be written to:" -ForegroundColor Green
Write-Host "       $LogFile" -ForegroundColor White
Write-Host ""
