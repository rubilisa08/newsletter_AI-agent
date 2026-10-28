# Removes the daily newsletter scheduled task.
#   powershell -ExecutionPolicy Bypass -File scripts\unregister_task.ps1

Unregister-ScheduledTask -TaskName "AI Newsletter Agent" -Confirm:$false
