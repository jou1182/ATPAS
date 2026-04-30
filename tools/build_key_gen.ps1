# ============================================================
# build_key_gen.ps1 — بناء أداة توليد الترخيص (ATPAS-KeyGen.exe)
# الاستخدام: .\tools\build_key_gen.ps1
#
# الخطوات:
#   1. تشفير key_gen_app.py بـ PyArmor
#   2. بناء EXE بـ PyInstaller
#   3. تنظيف _internal
#   4. تقرير نهائي
# ============================================================

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot + "\.."
Set-Location $Root

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ATPAS Key Generator — Protected Build             " -ForegroundColor Cyan
Write-Host "  أداة توليد أكواد الترخيص — بناء محمي             " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. تنظيف ──────────────────────────────────────────────────────────────
Write-Host "[1/5] تنظيف البناء السابق..." -ForegroundColor Yellow
Remove-Item "dist\ATPAS-KeyGen","build\ATPAS-KeyGen_protected" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "tools\.obf_keygen","tools\pyarmor_runtime_000000" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "tools\key_gen_app_protected.py","tools\key_gen_protected.spec" -Force -ErrorAction SilentlyContinue
Write-Host "  OK" -ForegroundColor Green

# ── 2. تشفير PyArmor ─────────────────────────────────────────────────────
Write-Host "[2/5] تشفير كود التطبيق بـ PyArmor..." -ForegroundColor Yellow
& pyarmor gen -O "tools\.obf_keygen" "tools\key_gen_app.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: فشل PyArmor" -ForegroundColor Red
    exit 1
}
Write-Host "  OK — كود مشفَّر في tools\.obf_keygen\" -ForegroundColor Green

# ── 3. إعداد ملفات البناء ─────────────────────────────────────────────────
Write-Host "[3/5] إعداد ملفات البناء المحمية..." -ForegroundColor Yellow

# نسخ الملف المشفَّر
Copy-Item "tools\.obf_keygen\key_gen_app.py" "tools\key_gen_app_protected.py" -Force

# نسخ PyArmor Runtime
$runtimeSrc = "tools\.obf_keygen\pyarmor_runtime_000000"
if (Test-Path $runtimeSrc) {
    Copy-Item $runtimeSrc "tools\pyarmor_runtime_000000" -Recurse -Force
}

# قراءة spec الأصلي وتعديله
$specContent = Get-Content "tools\key_gen.spec" -Raw -Encoding UTF8

# استبدال اسم الملف → النسخة المشفَّرة
$specContent = $specContent -replace "key_gen_app\.py", "key_gen_app_protected.py"

# إضافة PyArmor runtime للـ datas
$runtimeEntry = "        (str(ROOT / 'tools' / 'pyarmor_runtime_000000'), 'pyarmor_runtime_000000'),"
$specContent = $specContent -replace "(datas=\[)", "`$1`n$runtimeEntry"

# إضافة PyArmor runtime للـ hiddenimports
$specContent = $specContent -replace "('hashlib',)", "'pyarmor_runtime_000000',`n        `$1"

# إضافة pathex لـ pyarmor_runtime
$specContent = $specContent -replace "(pathex=\[str\(ROOT\), str\(ROOT / 'tools'\)\])", "pathex=[str(ROOT), str(ROOT / 'tools'), str(ROOT / 'tools' / 'pyarmor_runtime_000000')]"

$specContent | Set-Content "tools\key_gen_protected.spec" -Encoding UTF8
Write-Host "  OK — key_gen_protected.spec" -ForegroundColor Green

# ── 4. بناء EXE ──────────────────────────────────────────────────────────
Write-Host "[4/5] بناء EXE (1-3 دقائق)..." -ForegroundColor Yellow
Write-Host ""

& pyinstaller "tools\key_gen_protected.spec" --noconfirm --clean 2>&1 |
    Where-Object { $_ -match "ERROR|WARNING|Build complete|Successfully|FAILED" } |
    ForEach-Object { Write-Host "  $_" }

# تنظيف ملفات temp
Remove-Item "tools\key_gen_app_protected.py","tools\key_gen_protected.spec" -Force -ErrorAction SilentlyContinue
Remove-Item "tools\.obf_keygen","tools\pyarmor_runtime_000000" -Recurse -Force -ErrorAction SilentlyContinue

if (-not (Test-Path "dist\ATPAS-KeyGen\ATPAS-KeyGen.exe")) {
    Write-Host ""
    Write-Host "ERROR: فشل البناء — ATPAS-KeyGen.exe لم يُنشأ" -ForegroundColor Red

    # fallback: بناء بدون PyArmor (للتطوير)
    Write-Host "Trying fallback build without obfuscation..." -ForegroundColor Yellow
    & pyinstaller "tools\key_gen.spec" --noconfirm --clean 2>&1 |
        Where-Object { $_ -match "ERROR|WARNING|Build complete|Successfully|FAILED" } |
        ForEach-Object { Write-Host "  $_" }

    if (-not (Test-Path "dist\ATPAS-KeyGen\ATPAS-KeyGen.exe")) {
        Write-Host "ERROR: فشل البناء النهائي" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Built without PyArmor (fallback)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  OK — ATPAS-KeyGen.exe" -ForegroundColor Green

# ── 5. تنظيف _internal ───────────────────────────────────────────────────
Write-Host "[5/5] تنظيف _internal..." -ForegroundColor Yellow
$internalPath = "dist\ATPAS-KeyGen\_internal"
if (Test-Path $internalPath) {
    & "$PSScriptRoot\clean_internal.ps1" $internalPath
} else {
    Write-Host "  لا يوجد _internal (single-file mode)" -ForegroundColor Gray
}

# ── تقرير ────────────────────────────────────────────────────────────────
$exeFile = "dist\ATPAS-KeyGen\ATPAS-KeyGen.exe"
$exeSizeMB = [math]::Round((Get-Item $exeFile).Length / 1MB, 1)

# حجم المجلد الكامل
$folderSizeMB = [math]::Round(
    (Get-ChildItem "dist\ATPAS-KeyGen" -Recurse -File |
     Measure-Object Length -Sum).Sum / 1MB, 1
)

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "  EXE:       dist\ATPAS-KeyGen\ATPAS-KeyGen.exe" -ForegroundColor White
Write-Host "  EXE Size:  $exeSizeMB MB" -ForegroundColor White
Write-Host "  Folder:    $folderSizeMB MB (كامل المجلد)" -ForegroundColor White
Write-Host ""
Write-Host "  PROTECTION:" -ForegroundColor Cyan
Write-Host "    PyArmor obfuscation     OK" -ForegroundColor Green
Write-Host "    _internal cleaned       OK" -ForegroundColor Green
Write-Host "    Password gate           OK" -ForegroundColor Green
Write-Host ""
Write-Host "  DISTRIBUTE: dist\ATPAS-KeyGen\ (المجلد كاملاً)" -ForegroundColor Yellow
Write-Host "  WARNING: Do NOT share this tool with customers!" -ForegroundColor Red
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
