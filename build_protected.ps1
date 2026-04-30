# ============================================================
# build_protected.ps1 — بناء ATPAS.exe مع حماية PyArmor
# الاستخدام: .\build_protected.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  ATPAS Protected Build — PyArmor + PyInstaller" -ForegroundColor Cyan
Write-Host "=====================================================`n" -ForegroundColor Cyan

Set-Location $Root

# ── 1. تشفير الملفات الحساسة ─────────────────────────────────────────
Write-Host "[1/5] تشفير الملفات الحساسة بـ PyArmor..." -ForegroundColor Yellow

$CriticalFiles = @(
    "utils\license_manager.py",
    "ui\activation_dialog.py",
    "main.py"
)

# نسخ احتياطية
foreach ($f in $CriticalFiles) {
    Copy-Item $f "$f.bak" -Force
}

# تشفير
Remove-Item ".obf" -Recurse -Force -ErrorAction SilentlyContinue
$obfResult = pyarmor gen -O .obf $CriticalFiles 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ فشل PyArmor — استعادة الملفات الأصلية..." -ForegroundColor Red
    foreach ($f in $CriticalFiles) { Copy-Item "$f.bak" $f -Force; Remove-Item "$f.bak" -Force }
    exit 1
}
Write-Host "  ✅ تم تشفير $($CriticalFiles.Count) ملفات" -ForegroundColor Green

# ── 2. نسخ الملفات المشفّرة إلى أماكنها ──────────────────────────────
Write-Host "[2/5] تطبيق الملفات المشفّرة..." -ForegroundColor Yellow

Copy-Item ".obf\license_manager.py"   "utils\license_manager.py" -Force
Copy-Item ".obf\activation_dialog.py" "ui\activation_dialog.py"  -Force
Copy-Item ".obf\main.py"              "main.py"                   -Force

# نسخ PyArmor Runtime
Remove-Item "pyarmor_runtime_000000" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ".obf\pyarmor_runtime_000000" "pyarmor_runtime_000000" -Recurse -Force
Write-Host "  ✅ تم نسخ runtime" -ForegroundColor Green

# ── 3. حذف مجلد dist القديم ──────────────────────────────────────────
Write-Host "[3/5] تنظيف البناء السابق..." -ForegroundColor Yellow
Remove-Item "dist\ATPAS","build\atpas" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  ✅ تم التنظيف" -ForegroundColor Green

# ── 4. البناء مع PyInstaller ─────────────────────────────────────────
Write-Host "[4/5] البناء مع PyInstaller..." -ForegroundColor Yellow
pyinstaller atpas.spec 2>&1 | Where-Object { $_ -match "(ERROR|Build complete|failed)" } | Write-Host

if (-not (Test-Path "dist\ATPAS\ATPAS.exe")) {
    Write-Host "❌ فشل البناء — استعادة الملفات الأصلية..." -ForegroundColor Red
    foreach ($f in $CriticalFiles) { Copy-Item "$f.bak" $f -Force; Remove-Item "$f.bak" -Force }
    exit 1
}

$ExeSize = [math]::Round((Get-Item "dist\ATPAS\ATPAS.exe").Length / 1MB, 1)
Write-Host "  ✅ ATPAS.exe — $ExeSize MB" -ForegroundColor Green

# ── 5. استعادة الملفات الأصلية ───────────────────────────────────────
Write-Host "[5/5] استعادة الملفات الأصلية للتطوير..." -ForegroundColor Yellow
foreach ($f in $CriticalFiles) {
    Copy-Item "$f.bak" $f -Force
    Remove-Item "$f.bak" -Force
}
Write-Host "  ✅ تم استعادة الكود الأصلي" -ForegroundColor Green

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "  ✅ البناء الآمن اكتمل — dist\ATPAS\" -ForegroundColor Green
Write-Host "  🔒 الملفات المحمية: license_manager | activation_dialog | main" -ForegroundColor Green
Write-Host "=====================================================`n" -ForegroundColor Green
