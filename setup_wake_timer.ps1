$taskName = "FoodMonitorWake"

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
} catch { }

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c exit"
$trigger = New-ScheduledTaskTrigger -Daily -At "08:55"
$settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Wake PC for food news push at 9am"

Write-Host "DONE: Wake timer set for 08:55 daily"
