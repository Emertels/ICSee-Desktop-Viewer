@echo off
cd /d "%~dp0"
if exist "dist\ICSee_Viewer\ICSee_Viewer.exe" (
    start "" "dist\ICSee_Viewer\ICSee_Viewer.exe"
) else (
    start "" pythonw "app.py"
)
exit
