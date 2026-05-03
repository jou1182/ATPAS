param(
    [string]$Message = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$script:TempStashCreated = $false

function Restore-TempStash {
    if (-not $script:TempStashCreated) {
        return
    }

    Write-Host ""
    Write-Host "Restoring local skipped files..." -ForegroundColor Yellow
    & git stash pop
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[WARNING] Could not restore the temporary stash automatically." -ForegroundColor Yellow
        Write-Host "Run this command manually after checking the repository:" -ForegroundColor Yellow
        Write-Host "  git stash list" -ForegroundColor Yellow
        Write-Host "  git stash pop" -ForegroundColor Yellow
        Write-Host ""
    } else {
        $script:TempStashCreated = $false
    }
}

function Stop-WithMessage([string]$MessageText) {
    Restore-TempStash
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

Write-Host "[1/6] Current working tree summary:" -ForegroundColor Yellow
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

Write-Host "[2/6] Staging safe project files..." -ForegroundColor Yellow
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

$DidCommit = $false

if ($SafeFiles.Count -eq 0) {
    Write-Host "[OK] No safe file changes to stage." -ForegroundColor Green
} else {
    $StageArgs = @("add", "--all", "--") + $SafeFiles
    Invoke-Git @StageArgs
}

$Staged = @(& git diff --cached --name-only)
if ($Staged.Count -gt 0) {
    Write-Host "Files to upload:" -ForegroundColor Green
    $Staged | ForEach-Object { Write-Host "  - $_" }
    Write-Host ""

    Write-Host "[3/6] Creating commit..." -ForegroundColor Yellow
    Invoke-Git commit -m $Message
    $DidCommit = $true
} else {
    Write-Host "[3/6] Creating commit..." -ForegroundColor Yellow
    Write-Host "No new commit needed. Existing local commits will still be pushed." -ForegroundColor Green
}

Write-Host "[4/6] Parking skipped local files..." -ForegroundColor Yellow
$TrackedDirtyAfterCommit = @(& git ls-files --modified --deleted)
$TrackedBlockedDirty = @()
foreach ($File in $TrackedDirtyAfterCommit) {
    $Normalized = $File.Replace("\", "/")
    if (Test-BlockedPath $Normalized) {
        $TrackedBlockedDirty += $File
    }
}

if ($TrackedBlockedDirty.Count -gt 0) {
    $TempStashName = "ATPAS safe upload temp stash $Now"
    $StashArgs = @("stash", "push", "-m", $TempStashName, "--") + $TrackedBlockedDirty
    $StashOutput = @(& git @StashArgs)
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Could not create a temporary stash for skipped local files."
    }
    if (($StashOutput -join "`n") -notmatch "No local changes") {
        $script:TempStashCreated = $true
        Write-Host "Tracked skipped files were parked temporarily." -ForegroundColor Green
    } else {
        Write-Host "No tracked skipped files needed parking." -ForegroundColor Green
    }
} else {
    Write-Host "No tracked skipped files needed parking." -ForegroundColor Green
}

Write-Host "[5/6] Syncing with GitHub..." -ForegroundColor Yellow
Invoke-Git pull --rebase origin $Branch

Write-Host "[6/6] Pushing to GitHub..." -ForegroundColor Yellow
Invoke-Git push -u origin $Branch

Restore-TempStash

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Upload completed successfully." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
