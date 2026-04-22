@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM ── تأكّد أن الـ bat يعمل من مجلد المشروع دائماً ──────────────────
cd /d "%~dp0"

echo ============================================================
echo    ATPAS v3.1 - بناء ملف EXE التنفيذي
echo    %DATE%  %TIME%
echo ============================================================
echo.

REM ── 1. إغلاق أي نسخة تشغيل حالية لفك القفل عن الملف ──────────────
echo [1/6] إغلاق أي نسخة ATPAS مفتوحة...
taskkill /f /im ATPAS.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM ── 2. حذف البناء السابق ───────────────────────────────────────────
echo [2/6] حذف البناء السابق...
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
echo [3/6] مسح ملفات الكاش القديمة...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)

REM ── 4. كتابة طابع البناء في version.json ───────────────────────────
echo [4/6] كتابة طابع تاريخ ووقت البناء...

REM استخراج التاريخ والوقت بصيغة موحدة
for /f "tokens=1-3 delims=/" %%a in ("%DATE:~0,10%") do (
    set BUILD_DATE=%%c-%%a-%%b
)

REM تنسيق الوقت
set BUILD_TIME=%TIME:~0,8%
set BUILD_TIME=%BUILD_TIME: =0%

REM بناء رقم الإصدار الكامل: 3.1.YYYYMMDD
set BUILD_TAG=3.1.%DATE:~6,4%%DATE:~0,2%%DATE:~3,2%

REM كتابة ملف version.json
(
echo {
echo   "version": "3.1",
echo   "build_date": "%DATE:~6,4%-%DATE:~0,2%-%DATE:~3,2%",
echo   "build_time": "%BUILD_TIME%",
echo   "build_label": "الرواف ATPAS v3.1 — مبني في %DATE:~6,4%/%DATE:~0,2%/%DATE:~3,2%",
echo   "build_tag": "%BUILD_TAG%"
echo }
) > version.json

echo    version.json كُتب بنجاح: v3.1 — %DATE%
echo.

REM ── 5. إنشاء مجلدات الإخراج ────────────────────────────────────────
if not exist output\generated_documents mkdir output\generated_documents
if not exist output\audit_trail          mkdir output\audit_trail
if not exist output\logs                 mkdir output\logs
if not exist output\reports              mkdir output\reports

REM ── 6. البناء ───────────────────────────────────────────────────────
echo [5/6] جاري البناء (قد يستغرق 2-4 دقائق)...
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

REM ── 7. التحقق من نجاح البناء ───────────────────────────────────────
echo [6/6] التحقق من الملف الناتج...
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
echo   [نجح البناء] ✓
echo   الملف:   dist\ATPAS\ATPAS.exe
echo   الإصدار: v3.1 — %DATE%  %TIME:~0,8%
echo   الحجم:   !EXE_MB! MB
echo.
echo   ⚠️  للتوزيع على أجهزة أخرى:
echo       انسخ مجلد dist\ATPAS بالكامل (ليس ملف EXE فقط)
echo       عند كل تحديث في الكود: أعد تشغيل هذا الملف أولاً
echo ============================================================
echo.

REM سؤال: هل تريد تشغيل التطبيق الآن؟
set /p LAUNCH="تشغيل التطبيق الآن؟ (y/n): "
if /i "!LAUNCH!"=="y" start "" "dist\ATPAS\ATPAS.exe"

pause
