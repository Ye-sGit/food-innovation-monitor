@echo off
echo 正在将食品热点监测添加到开机自启...
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_FILE=C:\Users\IceLand\food-innovation-monitor\startup.vbs
set SHORTCUT=%STARTUP_DIR%\食品热点监测.lnk

:: 创建 VBS 快捷方式到启动文件夹
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%VBS_FILE%'; $s.WorkingDirectory = 'C:\Users\IceLand\food-innovation-monitor'; $s.WindowStyle = 7; $s.Description = '食品饮料创新热点每日推送'; $s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo ✅ 开机自启设置成功！
    echo.
    echo 工作流程：
    echo   1. 每天开机后自动启动（后台静默）
    echo   2. 等待到早上 09：00
    echo   3. 采集热点 → 评分 → 推送飞书
    echo   4. 推送完成后自动退出
    echo.
) else (
    echo ❌ 设置失败，请以管理员身份运行
)

pause
