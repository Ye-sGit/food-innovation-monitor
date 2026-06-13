$ws = New-Object -ComObject WScript.Shell
$startup = [Environment]::GetFolderPath('Startup')
$sp = Join-Path $startup 'FoodMonitor.lnk'

if (Test-Path $sp) {
    Remove-Item $sp -Force
    Write-Host "Removed old shortcut"
}

$s = $ws.CreateShortcut($sp)
$s.TargetPath = 'C:\Users\IceLand\food-innovation-monitor\startup.vbs'
$s.WorkingDirectory = 'C:\Users\IceLand\food-innovation-monitor'
$s.WindowStyle = 7
$s.Save()

Write-Host "Shortcut created: $sp"
Write-Host "Working directory: $($s.WorkingDirectory)"
