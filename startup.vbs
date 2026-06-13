' 开机自启脚本 — 静默启动 Python，无命令行窗口
' 不关机时持续后台运行，每天 09:00 自动推送

Set WshShell = CreateObject("WScript.Shell")

PythonPath = "C:\Users\IceLand\AppData\Local\Programs\Python\Python312\python.exe"
ScriptPath = "C:\Users\IceLand\food-innovation-monitor\scheduler.py"
WorkDir = "C:\Users\IceLand\food-innovation-monitor"

WshShell.CurrentDirectory = WorkDir
WshShell.Run """" & PythonPath & """ """ & ScriptPath & """", 0, False
Set WshShell = Nothing
