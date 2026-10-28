# Registers a Windows scheduled task that runs the newsletter agent every day at 07:30.
# Re-running this script overwrites the existing task.
#   powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1

$TaskName = "AI Newsletter Agent"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $Python)) {
    throw "pythonw.exe not found: $Python (run 'uv sync' first)"
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument "main.py" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At "07:30"
# StartWhenAvailable: if the PC was off/asleep at 07:30, run as soon as it is back.
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Collect, select, summarize, verify and publish 5 AI news items to Discord" -Force | Out-Null

Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime, LastRunTime, LastTaskResult
