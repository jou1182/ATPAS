@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM ── تأكّد أن الـ bat يعمل من مجلد المشروع دائماً ──────────────────
cd /d "%~dp0"

echo ============================================================
echo    ATPAS v3.0 - بناء ملف EXE التنفيذي
echo    %DATE%  %TIME%
echo ============================================================
echo.

REM ── 1. إغلاق أي نسخة تشغيل حالية لفك القفل عن الملف ──────────────
echo [1/5] إغلاق أي نسخة ATPAS مفتوحة...
taskkill /f /im ATPAS.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM ── 2. حذف البناء السابق ───────────────────────────────────────────
echo [2/5] حذف البناء السابق...
if exist dist\ATPAS (
    rmdir /s /q dist\ATPAS
    if exist dist\ATPAS (
        echo [خطأ] تعذّر حذف dist\ATPAS - تأكّد أن ATPAS.exe ليس قيد التشغيل
        pause
        exit /b 1
    )
)
if exist build\ATPAS rmdir /s /q build\ATPAS

REM ── 3. مسح __pycache__ لضمان أحدث كود ────────────────────────────
echo [3/5] مسح ملفات الكاش القديمة...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)

REM ── 4. إنشاء مجلدات الإخراج ────────────────────────────────────────
if not exist output\generated_documents mkdir output\generated_documents
if not exist output\audit_trail          mkdir output\audit_trail
if not exist output\logs                 mkdir output\logs
if not exist output\reports              mkdir output\reports

REM ── 5. البناء ───────────────────────────────────────────────────────
echo [4/5] جاري البناء (قد يستغرق 2-4 دقائق)...
echo.
pyinstaller atpas.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [خطأ] فشل البناء - راجع الأخطاء أعلاه
    echo ============================================================
    pause
    exit /b 1
)

REM ── 6. التحقق من نجاح البناء ───────────────────────────────────────
echo [5/5] التحقق من الملف الناتج...
if not exist "dist\ATPAS\ATPAS.exe" (
    echo [خطأ] الملف dist\ATPAS\ATPAS.exe غير موجود رغم نجاح PyInstaller!
    pause
    exit /b 1
)

REM احسب حجم الملف
for %%A in ("dist\ATPAS\ATPAS.exe") do set EXE_SIZE=%%~zA
set /a EXE_MB=!EXE_SIZE! / 1048576

echo.
echo ============================================================
echo   [نجح البناء]
echo   الملف: dist\ATPAS\ATPAS.exe
echo   الحجم: !EXE_MB! MB
echo   التاريخ: %DATE%  %TIME%
echo.
echo   لتشغيل التطبيق:   dist\ATPAS\ATPAS.exe
echo   للتوزيع: انسخ مجلد dist\ATPAS بالكامل
echo ============================================================
echo.

REM سؤال: هل تريد تشغيل التطبيق الآن؟
set /p LAUNCH="تشغيل التطبيق الآن؟ (y/n): "
if /i "!LAUNCH!"=="y" start "" "dist\ATPAS\ATPAS.exe"

pause
