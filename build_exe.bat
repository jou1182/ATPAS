@echo off
setlocal enabledelayedexpansion

REM -- Always run from project folder --
cd /d "%~dp0"

echo ============================================================
echo    ATPAS v3.2 - Build EXE
echo    %DATE%  %TIME%
echo ============================================================
echo.

REM -- Show last build info --
if exist dist\ATPAS\ATPAS.exe (
    for %%F in (dist\ATPAS\ATPAS.exe) do (
        echo   Last EXE: %%~tF   Size: %%~zF bytes
    )
    echo   Will be replaced now.
) else (
    echo   No previous EXE found - fresh build.
)
echo.

REM -- 1. Kill any running instance --
echo [1/6] Closing any running ATPAS instance...
taskkill /f /im ATPAS.exe >nul 2>&1
powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul

REM -- 2. Delete previous build (PowerShell to bypass permission errors) --
echo [2/6] Deleting previous build...
if exist dist\ATPAS (
    powershell -Command "Remove-Item -Path 'dist\ATPAS' -Recurse -Force -ErrorAction SilentlyContinue"
    if exist dist\ATPAS (
        echo [ERROR] Cannot delete dist\ATPAS - make sure ATPAS.exe is not running.
        pause
        exit /b 1
    )
)
if exist build (
    powershell -Command "Remove-Item -Path 'build' -Recurse -Force -ErrorAction SilentlyContinue"
)

REM -- 3. Clear __pycache__ --
echo [3/6] Clearing cache files...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)

REM -- 4. Write build stamp to version.json --
echo [4/6] Writing build timestamp...

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set BUILD_DATE=%%i
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format HH:mm:ss"') do set BUILD_TIME=%%i
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set BUILD_TAG=3.2.%%i

(
echo {
echo   "version": "3.2",
echo   "build_date": "%BUILD_DATE%",
echo   "build_time": "%BUILD_TIME%",
echo   "build_label": "ATPAS v3.2 built on %BUILD_DATE%",
echo   "build_tag": "%BUILD_TAG%"
echo }
) > version.json

echo    version.json written: v3.2 -- %BUILD_DATE%
echo.

REM -- 5. Create output directories --
if not exist output\generated_documents mkdir output\generated_documents
if not exist output\audit_trail          mkdir output\audit_trail
if not exist output\logs                 mkdir output\logs
if not exist output\reports              mkdir output\reports

REM -- 6. Build --
echo [5/6] Building EXE (may take 2-4 minutes)...
echo.
pyinstaller atpas.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERROR] Build failed - check errors above
    echo ============================================================
    pause
    exit /b 1
)

REM -- 7. Verify output --
echo [6/6] Verifying output...
if not exist "dist\ATPAS\ATPAS.exe" (
    echo [ERROR] dist\ATPAS\ATPAS.exe not found after build!
    pause
    exit /b 1
)

for %%A in ("dist\ATPAS\ATPAS.exe") do set EXE_SIZE=%%~zA
set /a EXE_MB=!EXE_SIZE! / 1048576

echo.
echo ============================================================
echo   [SUCCESS] Build complete!
echo   File:    dist\ATPAS\ATPAS.exe
echo   Version: v3.2 -- %DATE%  %TIME:~0,8%
echo   Size:    !EXE_MB! MB
echo.
echo   NOTE: To distribute, copy the entire dist\ATPAS folder,
echo         not just the EXE file.
echo ============================================================
echo.

if /i "%ATPAS_BUILD_NO_PROMPT%"=="1" exit /b 0

set /p LAUNCH="Launch the app now? (y/n): "
if /i "!LAUNCH!"=="y" start "" "dist\ATPAS\ATPAS.exe"

pause
