@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   ATPAS - GitHub Backup
echo ============================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not available in PATH.
    echo Install Git for Windows, then run this file again.
    echo.
    pause
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This folder is not a Git repository.
    echo Folder: %CD%
    echo.
    pause
    exit /b 1
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git remote "origin" is not configured.
    echo Add a GitHub remote first, then run this file again.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set BRANCH=%%B
if "%BRANCH%"=="" (
    echo [ERROR] Could not detect the current Git branch.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"') do set NOW=%%T

echo Repository: %CD%
echo Branch:     %BRANCH%
echo Remote:     origin
echo Time:       %NOW%
echo.

echo [1/4] Adding project changes...
git add -A
if errorlevel 1 goto :fail

git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo [OK] No new changes to back up. GitHub is already up to date.
    echo.
    pause
    exit /b 0
)

echo [2/4] Creating backup commit...
git commit -m "Backup ATPAS %NOW%"
if errorlevel 1 goto :fail

echo [3/4] Syncing with GitHub...
git pull --rebase origin %BRANCH%
if errorlevel 1 (
    echo.
    echo [ERROR] Could not sync with GitHub before pushing.
    echo Resolve the Git message above, then run this file again.
    echo.
    pause
    exit /b 1
)

echo [4/4] Uploading backup to GitHub...
git push -u origin %BRANCH%
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo   Backup completed successfully on GitHub.
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo ============================================================
echo   Backup failed. Review the Git message above.
echo ============================================================
echo.
pause
exit /b 1
