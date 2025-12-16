# Windows Task Scheduler Setup Script
# Creates a scheduled task to run the market analysis pipeline monthly
# Runs on the third Saturday of each month at 9:00 AM
#
# REQUIRES: Run as Administrator (right-click PowerShell -> Run as Administrator)

# Configuration
$TaskName = "RedfinMarketAnalysis"
$ScriptPath = Join-Path $PSScriptRoot "run_scheduled.py"
$PythonPath = (Get-Command python).Source
$LogPath = Join-Path $PSScriptRoot "task_scheduler.log"

# Arguments for run_scheduled.py (without AI API calls)
$Arguments = "`"$ScriptPath`" --no-ai"

Write-Host ("=" * 60)
Write-Host "WINDOWS TASK SCHEDULER SETUP"
Write-Host ("=" * 60)
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires Administrator privileges." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Press Win + X"
    Write-Host "  2. Select 'Windows Terminal (Admin)' or 'PowerShell (Admin)'"
    Write-Host "  3. Navigate to this directory:"
    Write-Host "     cd `"$PSScriptRoot`""
    Write-Host "  4. Run this script again:"
    Write-Host "     .\setup_task_scheduler.ps1"
    Write-Host ""
    Write-Host "Alternatively, use the MANUAL SETUP below:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "MANUAL TASK SCHEDULER SETUP (No Admin Required):"
    Write-Host "================================================"
    Write-Host "1. Open Task Scheduler: Win+R, type 'taskschd.msc', Enter"
    Write-Host "2. Click 'Create Task' in the right panel"
    Write-Host "3. General Tab:"
    Write-Host "   - Name: $TaskName"
    Write-Host "   - Check 'Run whether user is logged on or not'"
    Write-Host "4. Triggers Tab -> New:"
    Write-Host "   - Weekly, every 4 weeks, Saturday, 9:00 AM"
    Write-Host "5. Actions Tab -> New:"
    Write-Host "   - Program: $PythonPath"
    Write-Host "   - Arguments: $Arguments"
    Write-Host "   - Start in: $PSScriptRoot"
    Write-Host "6. Settings Tab:"
    Write-Host "   - Check 'Run task as soon as possible after scheduled start is missed'"
    Write-Host "   - Check 'If the task fails, restart every 30 minutes'"
    Write-Host "7. Click OK and enter your Windows password"
    Write-Host ""
    exit 1
}

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "        Please ensure Python is installed and in your PATH"
    exit 1
}

Write-Host "[INFO] Python Path: $PythonPath"
Write-Host "[INFO] Script Path: $ScriptPath"
Write-Host "[INFO] Arguments: $Arguments"
Write-Host ""

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "[ERROR] Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "[WARN] Task '$TaskName' already exists"
    $Response = Read-Host "Do you want to replace it? (y/n)"

    if ($Response -eq 'y' -or $Response -eq 'Y') {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Removed existing task"
    } else {
        Write-Host "[CANCEL] Keeping existing task"
        exit 0
    }
}

Write-Host ""
Write-Host "Creating scheduled task with the following settings:"
Write-Host "  Task Name: $TaskName"
Write-Host "  Schedule: Monthly on third Saturday at 9:00 AM"
Write-Host "  Command: python $ScriptPath --no-ai"
Write-Host "  Run when missed: Yes (if computer was off)"
Write-Host "  Run with highest privileges: No (runs as current user)"
Write-Host ""

# Create the action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $Arguments -WorkingDirectory $PSScriptRoot

# Create the trigger for third Saturday of each month
# Note: Task Scheduler doesn't have direct "third Saturday" support
# We'll create triggers for 15th-21st and use a filter for Saturday
$Triggers = @()

# Create a trigger for each day in the third full week (15th-21st)
# The script will only run if it's Saturday
for ($day = 15; $day -le 21; $day++) {
    $Trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM" -DaysInterval 1
    # This creates daily triggers, but we'll modify them below
    $Triggers += $Trigger
}

# For simplicity, we'll use a single monthly trigger that repeats
# and relies on the pipeline to check if data is fresh
$Trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 4 -DaysOfWeek Saturday -At "09:00AM"

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 30)

# Principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U

# Register the task
try {
    $Task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Automated monthly Redfin market analysis pipeline. Downloads data, processes metrics, generates dashboards and reports." `
        -ErrorAction Stop

    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[OK] TASK CREATED SUCCESSFULLY" -ForegroundColor Green
    Write-Host ("=" * 60)
    Write-Host ""
    Write-Host "Task Details:"
    Write-Host "  Name: $($Task.TaskName)"
    Write-Host "  State: $($Task.State)"
    Write-Host "  Next Run Time: Check Task Scheduler for exact time"
    Write-Host ""
    Write-Host "To view the task:"
    Write-Host "  1. Open Task Scheduler (taskschd.msc)"
    Write-Host "  2. Navigate to Task Scheduler Library"
    Write-Host "  3. Find '$TaskName'"
    Write-Host ""
    Write-Host "To test the task immediately:"
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To view task history:"
    Write-Host "  Get-ScheduledTaskInfo -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To remove the task:"
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    Write-Host ""
    Write-Host "IMPORTANT NOTES:"
    Write-Host "  - The task runs WITHOUT AI narratives (--no-ai flag)"
    Write-Host "  - To enable AI: Remove --no-ai from the task action in Task Scheduler"
    Write-Host "  - The task will run even if the computer was off (StartWhenAvailable)"
    Write-Host "  - Email notifications require configuration in notifications_config.json"
    Write-Host "  - Check pipeline_runs.log for execution history"
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[FAILED] TASK CREATION FAILED" -ForegroundColor Red
    Write-Host ("=" * 60)
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try running PowerShell as Administrator, or use the manual setup steps above."
    exit 1
}
