# ============================================================
# clean_internal.ps1 -- Remove unnecessary files from _internal
#
# Usage:
#   .\clean_internal.ps1 "dist\ATPAS-KeyGen\_internal"
#   .\clean_internal.ps1 "dist\ATPAS\_internal"
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$InternalPath
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path $InternalPath)) {
    Write-Host "  [SKIP] _internal not found: $InternalPath" -ForegroundColor Yellow
    exit 0
}

$beforeBytes = (Get-ChildItem $InternalPath -Recurse -File | Measure-Object Length -Sum).Sum
$script:removedCount = 0
$script:removedBytes = 0

function Remove-Pattern {
    param([string]$Path, [string]$Pattern, [string]$Reason)
    $files = Get-ChildItem $Path -Recurse -Filter $Pattern -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        $script:removedBytes += $f.Length
        $script:removedCount++
        Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
    }
    if ($files.Count -gt 0) {
        Write-Host "    Removed $($files.Count) x $Pattern  [$Reason]" -ForegroundColor DarkGray
    }
}

function Remove-Dir {
    param([string]$Path, [string]$DirName, [string]$Reason)
    $dirs = Get-ChildItem $Path -Recurse -Directory -Filter $DirName -ErrorAction SilentlyContinue
    foreach ($d in $dirs) {
        $sz = (Get-ChildItem $d.FullName -Recurse -File | Measure-Object Length -Sum).Sum
        $script:removedBytes += $sz
        $script:removedCount++
        Remove-Item $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($dirs.Count -gt 0) {
        Write-Host "    Removed $($dirs.Count) x $DirName\  [$Reason]" -ForegroundColor DarkGray
    }
}

Write-Host "  Scanning $InternalPath ..." -ForegroundColor Cyan

# 1. Python source files
Write-Host "  [1] Python source .py files ..." -ForegroundColor Yellow
Remove-Pattern $InternalPath "*.py"

# 2. Test files
Write-Host "  [2] Test files ..." -ForegroundColor Yellow
Remove-Pattern $InternalPath "test_*.*"
Remove-Pattern $InternalPath "*_test.*"
Remove-Pattern $InternalPath "pytest*"
Remove-Pattern $InternalPath "conftest*"

# 3. Documentation
Write-Host "  [3] Documentation files ..." -ForegroundColor Yellow
Remove-Pattern $InternalPath "*.md"
Remove-Pattern $InternalPath "*.rst"
Remove-Pattern $InternalPath "CHANGES*"
Remove-Pattern $InternalPath "LICENSE*"
Remove-Pattern $InternalPath "NOTICE*"
Remove-Pattern $InternalPath "COPYING*"
Remove-Pattern $InternalPath "AUTHORS*"
Remove-Pattern $InternalPath "README*"

# 4. Build / dev artifacts
Write-Host "  [4] Build artifacts ..." -ForegroundColor Yellow
Remove-Pattern $InternalPath "*.spec"
Remove-Pattern $InternalPath "setup.py"
Remove-Pattern $InternalPath "*.bat"
Remove-Pattern $InternalPath "*.sh"

# 5. Debug symbols
Write-Host "  [5] Debug symbols ..." -ForegroundColor Yellow
Remove-Pattern $InternalPath "*.pdb"
Remove-Pattern $InternalPath "*.ilk"
Remove-Pattern $InternalPath "*.map"

# 6. Unused folders
Write-Host "  [6] Unused folders ..." -ForegroundColor Yellow
Remove-Dir $InternalPath "__pycache__"
Remove-Dir $InternalPath "tests"
Remove-Dir $InternalPath "test"
Remove-Dir $InternalPath "docs"
Remove-Dir $InternalPath "examples"
Remove-Dir $InternalPath "samples"

# 7. Unused Qt plugins
Write-Host "  [7] Unused Qt plugins ..." -ForegroundColor Yellow
$unusedQt = @(
    "Qt5WebEngine*","Qt5Designer*","Qt5Quick*",
    "Qt5Bluetooth*","Qt5Location*","Qt5Multimedia*",
    "Qt5Nfc*","Qt5Sensors*","Qt5Test*","Qt5XmlPatterns*"
)
foreach ($p in $unusedQt) {
    Remove-Pattern $InternalPath $p
}

$afterBytes = (Get-ChildItem $InternalPath -Recurse -File | Measure-Object Length -Sum).Sum
$beforeMB   = [math]::Round($beforeBytes / 1MB, 1)
$afterMB    = [math]::Round($afterBytes  / 1MB, 1)
$savedMB    = [math]::Round(($beforeBytes - $afterBytes) / 1MB, 2)

Write-Host ""
Write-Host "  ----------------------------------------" -ForegroundColor Green
Write-Host "  _internal cleaned: $beforeMB MB -> $afterMB MB  (saved $savedMB MB)" -ForegroundColor Green
Write-Host "  ----------------------------------------" -ForegroundColor Green
