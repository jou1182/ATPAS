@echo off
cd /d "%~dp0"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\ATPAS (Dev).lnk'); $s.TargetPath = '%~dp0run_dev.bat'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%~dp0assets\atpas.ico'; $s.Description = 'ATPAS Development Mode'; $s.Save()"
echo Done - shortcut created on Desktop
pause
