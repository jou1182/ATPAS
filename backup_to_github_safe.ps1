param(
    [string]$Message = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Stop-WithMessage([string]$MessageText) {
    Write-Host ""
    Write-Host "[ERROR] $MessageText" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Git command failed: git $($Args -join ' ')"
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ATPAS - Safe GitHub Upload" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "Git is not installed or not available in PATH."
}

& git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "This folder is not a Git repository: $Root"
}

$RemoteUrl = (& git remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RemoteUrl)) {
    Stop-WithMessage 'Git remote "origin" is not configured.'
}

$Branch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($Branch)) {
    Stop-WithMessage "Could not detect the current Git branch."
}

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Backup ATPAS $Now"
}

Write-Host "Repository: $Root"
Write-Host "Branch:     $Branch"
Write-Host "Remote:     $RemoteUrl"
Write-Host "Message:    $Message"
Write-Host ""

Write-Host "[1/5] Current working tree summary:" -ForegroundColor Yellow
& git status --short
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] No files were staged, committed, or pushed." -ForegroundColor Yellow
    exit 0
}

$BlockedPatterns = @(
    "^dist/",
    "^build/",
    "^output/",
    "^\.claude/",
    "^templates/source_documents/",
    "^tools/generate_license\.py$",
    "^.*\.xlsx$",
    "^.*\.xls$",
    "^_owners_real\.json$",
    "^_owner_extract\.json$",
    "^\.atpas_sessions\.json$",
    "^build_history\.json$"
)

function Test-BlockedPath([string]$PathText) {
    $Normalized = $PathText.Replace("\", "/")
    foreach ($Pattern in $BlockedPatterns) {
        if ($Normalized -match $Pattern) {
            return $true
        }
    }
    return $false
}

Write-Host "[2/5] Staging safe project files..." -ForegroundColor Yellow
& git restore --staged -- . *> $null

$Candidates = @(& git ls-files --modified --deleted --others --exclude-standard)
$SafeFiles = @()
$Blocked = @()
foreach ($File in $Candidates) {
    $Normalized = $File.Replace("\", "/")
    if (Test-BlockedPath $Normalized) {
        $Blocked += $File
    } else {
        $SafeFiles += $File
    }
}

if ($Blocked.Count -gt 0) {
    Write-Host ""
    Write-Host "[SKIPPED] Sensitive or generated files were not staged:" -ForegroundColor Yellow
    $Blocked | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host ""
}

if ($SafeFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "[OK] No safe changes to upload. GitHub is already up to date." -ForegroundColor Green
    Write-Host ""
    exit 0
}

$StageArgs = @("add", "--all", "--") + $SafeFiles
Invoke-Git @StageArgs

$Staged = @(& git diff --cached --name-only)
if ($Staged.Count -eq 0) {
    Write-Host ""
    Write-Host "[OK] No safe changes to upload. GitHub is already up to date." -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "Files to upload:" -ForegroundColor Green
$Staged | ForEach-Object { Write-Host "  - $_" }
Write-Host ""

Write-Host "[3/5] Creating commit..." -ForegroundColor Yellow
Invoke-Git commit -m $Message

Write-Host "[4/5] Syncing with GitHub..." -ForegroundColor Yellow
Invoke-Git pull --rebase origin $Branch

Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
Invoke-Git push -u origin $Branch

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Upload completed successfully." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
