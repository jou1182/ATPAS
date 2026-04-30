@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0\.."

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   ATPAS Key Generator — Build Script               ║
echo ║   بناء أداة توليد أكواد الترخيص                    ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM ── 1. تنظيف البناء السابق ──────────────────────────────────────────────
echo [1/5]  تنظيف البناء السابق...
powershell -NoProfile -Command "Remove-Item -Path 'dist\ATPAS-KeyGen','build\ATPAS-KeyGen' -Recurse -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Remove-Item -Path 'tools\.obf_keygen' -Recurse -Force -ErrorAction SilentlyContinue"
echo        تم التنظيف

REM ── 2. تشفير الكود بـ PyArmor ────────────────────────────────────────────
echo.
echo [2/5]  تشفير الكود بـ PyArmor...
pyarmor gen -O "tools\.obf_keygen" "tools\key_gen_app.py"

if errorlevel 1 (
    echo.
    echo [ERROR] فشل PyArmor — تأكد من تثبيته: pip install pyarmor
    pause
    exit /b 1
)
echo        تم التشفير بنجاح

REM ── 3. نسخ الملف المشفَّر مؤقتاً ───────────────────────────────────────
echo.
echo [3/5]  تطبيق الكود المشفَّر...
copy /y "tools\.obf_keygen\key_gen_app.py" "tools\key_gen_app_protected.py" >nul

REM ── 4. البناء مع PyInstaller ────────────────────────────────────────────
echo.
echo [4/5]  البناء مع PyInstaller (1-2 دقيقة)...
echo.

REM نعدّل الـ spec مؤقتاً ليستخدم الملف المشفَّر
powershell -NoProfile -Command ^
    "(Get-Content 'tools\key_gen.spec') -replace 'key_gen_app\.py', 'key_gen_app_protected.py' | Set-Content 'tools\key_gen_protected.spec'"

REM نسخ PyArmor runtime إلى مجلد tools ليجده PyInstaller
powershell -NoProfile -Command ^
    "if (Test-Path 'tools\.obf_keygen\pyarmor_runtime_000000') { Copy-Item 'tools\.obf_keygen\pyarmor_runtime_000000' 'tools\pyarmor_runtime_000000' -Recurse -Force }"

REM تحديث الـ spec ليضيف PyArmor runtime
powershell -NoProfile -Command ^
    "(Get-Content 'tools\key_gen_protected.spec') -replace ^
    'hiddenimports=\[', ^
    'hiddenimports=[''pyarmor_runtime_000000'',' | Set-Content 'tools\key_gen_protected.spec'"

pyinstaller "tools\key_gen_protected.spec" --noconfirm --clean

REM تنظيف الملفات المؤقتة
del /q "tools\key_gen_app_protected.py" >nul 2>&1
del /q "tools\key_gen_protected.spec" >nul 2>&1
powershell -NoProfile -Command "Remove-Item 'tools\.obf_keygen' -Recurse -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Remove-Item 'tools\pyarmor_runtime_000000' -Recurse -Force -ErrorAction SilentlyContinue"

if not exist "dist\ATPAS-KeyGen\ATPAS-KeyGen.exe" (
    echo.
    echo [ERROR] فشل البناء — تحقق من الأخطاء أعلاه
    pause
    exit /b 1
)

REM ── 5. تنظيف _internal ──────────────────────────────────────────────────
echo.
echo [5/5]  تنظيف مجلد _internal...
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\clean_internal.ps1" "dist\ATPAS-KeyGen\_internal"

REM ── النتيجة ──────────────────────────────────────────────────────────────
echo.
for %%A in ("dist\ATPAS-KeyGen\ATPAS-KeyGen.exe") do set EXE_SIZE=%%~zA
set /a EXE_MB=!EXE_SIZE! / 1048576

echo ╔══════════════════════════════════════════════════════╗
echo ║   تم البناء بنجاح ✅                               ║
echo ║   الملف: dist\ATPAS-KeyGen\ATPAS-KeyGen.exe        ║
echo ║   الحجم: !EXE_MB! MB                               ║
echo ║                                                      ║
echo ║   ⚠  لا توزَّع هذه الأداة على العملاء!             ║
echo ╚══════════════════════════════════════════════════════╝
echo.

pause
