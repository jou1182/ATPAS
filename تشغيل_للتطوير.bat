@echo off
cd /d "%~dp0"
echo تشغيل ATPAS في وضع التطوير (بدون بناء EXE)...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo حدث خطأ - اضغط اي مفتاح للإغلاق
    pause
)
