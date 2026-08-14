# =====================================================================
#  ai-skills skill distribution script (single source of truth -> mirrors)
#
#  Source : <repo>\skills  +  assets\（repo = 本脚本所在目录，可 fork 到任意位置）
#  Targets: opencode / claude / codex / agents(DSH) / cc-switch（$HOME 自动探测）
#  Semantics: hash compare + mirror cleanup + orphan prune(-Prune) + git commit(-Commit)
#
#  Usage:
#    powershell -File .\sync.ps1
#    powershell -File .\sync.ps1 -Targets opencode,claude
#    powershell -File .\sync.ps1 -DryRun
#    powershell -File .\sync.ps1 -Prune
#    powershell -File .\sync.ps1 -Commit
# =====================================================================
param(
    [string[]]$Targets = @('opencode', 'claude', 'codex', 'agents', 'ccswitch'),
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Prune,     # delete orphan dirs in target that are absent from source
    [switch]$Commit     # git-commit the source after sync
)

$ErrorActionPreference = 'Stop'

# ---- single source of truth ----
$repo = $PSScriptRoot                      # 仓库根 = 本脚本所在目录（可 fork 到任意位置）
$src  = Join-Path $repo 'skills'

# ---- common skill list (9, identical for every target) ----
$common = @(
    'competition-workflow', 'guozhan-paper', 'linear-regression-hw',
    'math-modeling-paper', 'math-paper-template', 'sensitivity-analysis',
    'statistical-diagnosis', 'tex-pdf-image-to-word', 'vision-ocr'
)

# ---- distribution targets (skills dirs; $HOME-based so forks work out of the box) ----
$dest = @{
    opencode = Join-Path $HOME '.config\opencode\skills'
    claude   = Join-Path $HOME '.claude\skills'
    codex    = Join-Path $HOME '.codex\skills'
    agents   = Join-Path $HOME '.agents\skills'     # DSH + agents ecosystem shared root
    ccswitch = Join-Path $HOME '.cc-switch\skills'
}

# ---- how each tool picks up changes ----
$restartHint = @{
    opencode = 'opencode: restart session'
    claude   = 'Claude Code: restart session'
    codex    = 'Codex: restart session'
    agents   = 'DSH/agents: hot-reload (chokidar auto)'
    ccswitch = 'cc-switch: restart if resident'
}

# ---- assets targets (all five, skills reference ../../assets/...) ----
$assetTargets = @('opencode', 'claude', 'codex', 'agents', 'ccswitch')

function Get-FileHashMap {
    param([string]$Dir)
    $map = @{}
    if (Test-Path $Dir) {
        Get-ChildItem $Dir -Recurse -File | ForEach-Object {
            $rel = $_.FullName.Substring($Dir.Length).TrimStart('\')
            $map[$rel] = (Get-FileHash $_.FullName -Algorithm MD5).Hash
        }
    }
    return $map
}

$invalid = $Targets | Where-Object { -not $dest.ContainsKey($_) }
if ($invalid) {
    Write-Host "ERROR: unknown targets: $($invalid -join ', ') (valid: $($dest.Keys -join ', '))"
    exit 1
}

foreach ($t in $Targets) {
    $dst = $dest[$t]
    $allowed = @($common)

    Write-Host ''
    Write-Host "=== $t -> $dst ==="
    if (-not $DryRun) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }

    # ---- assets ----
    if ($t -in $assetTargets) {
        $assetSrc  = Join-Path $repo 'assets'
        $assetDst  = (Split-Path $dst -Parent) + '\assets'
        if (Test-Path $assetSrc) {
            $aChanged = $false
            if (-not (Test-Path $assetDst)) {
                if ($DryRun) { Write-Host '  [DIFF] assets (dir missing)' }
                else { New-Item -ItemType Directory -Path $assetDst -Force | Out-Null; $aChanged = $true }
            }
            Get-ChildItem $assetSrc -File | ForEach-Object {
                $df = Join-Path $assetDst $_.Name
                if (-not (Test-Path $df) -or (Get-FileHash $_.FullName -Algorithm MD5).Hash -ne (Get-FileHash $df -Algorithm MD5).Hash) {
                    if ($DryRun) { Write-Host "  [DIFF] assets\$($_.Name)" }
                    else { Copy-Item $_.FullName $assetDst -Force; $aChanged = $true }
                }
            }
            if (-not $DryRun -and $aChanged) { Write-Host '  [UPD] assets synced' }
        }
    }

    $created = 0; $updated = 0; $same = 0; $diff = 0
    foreach ($skill in $allowed) {
        $s = Join-Path $src $skill
        if (-not (Test-Path $s)) { Write-Warning "source missing: $skill"; continue }
        $srcMap = Get-FileHashMap -Dir $s
        $dstMap = Get-FileHashMap -Dir (Join-Path $dst $skill)

        if ($srcMap.Count -eq 0 -and $dstMap.Count -eq 0) { $same++; continue }

        $needsCopy = $false
        if ($srcMap.Count -ne $dstMap.Count) { $needsCopy = $true }
        else {
            foreach ($k in $srcMap.Keys) {
                if (-not $dstMap.ContainsKey($k) -or $dstMap[$k] -ne $srcMap[$k]) { $needsCopy = $true; break }
            }
        }

        if ($needsCopy) {
            $diff++
            # mirror cleanup: remove target files absent from source
            foreach ($k in $dstMap.Keys) {
                if (-not $srcMap.ContainsKey($k)) {
                    $stale = Join-Path (Join-Path $dst $skill) $k
                    if ($DryRun) { Write-Host "  [DEL] $skill\$k" }
                    else { Remove-Item -LiteralPath $stale -Force -ErrorAction SilentlyContinue; Write-Host "  [DEL] $skill\$k" }
                }
            }
            if ($DryRun) { Write-Host "  [DIFF] $skill" }
            else {
                Copy-Item -Path $s -Destination $dst -Recurse -Force
                if ($dstMap.Count -eq 0) { $created++ } else { $updated++ }
                Write-Host "  [$(if ($dstMap.Count -eq 0) {'NEW'} else {'UPD'})] $skill"
            }
        } else {
            $same++
        }
    }

    # ---- orphan dir detection / prune ----
    if (Test-Path $dst) {
        $central = @(Get-ChildItem $src -Directory | Select-Object -ExpandProperty Name)
        $orphans = Get-ChildItem $dst -Directory | Where-Object {
            $_.Name -notin $central -and $_.Name -notmatch '^\.' -and $_.Name -ne '.gitkeep'
        } | Select-Object -ExpandProperty Name
        if ($orphans) {
            if ($DryRun -or -not $Prune) {
                Write-Host "  [ORPHAN] local only: $($orphans -join ', ') $(if (-not $Prune) {'(use -Prune to delete)'})"
            }
            if ($Prune -and -not $DryRun) {
                foreach ($o in $orphans) {
                    Remove-Item -LiteralPath (Join-Path $dst $o) -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "  [PRUNE] removed orphan dir: $o"
                }
            }
        } else {
            Write-Host '  [OK] no orphan dirs'
        }
    }

    if (-not $DryRun) {
        Write-Host "  summary: $created new, $updated updated, $same identical"
        Write-Host "  hint: $($restartHint[$t])"
    } else {
        Write-Host "  summary: would copy $diff of $($allowed.Count), $same identical"
    }
}

# ---- optional git commit ----
if ($Commit -and -not $DryRun) {
    Write-Host ''
    Write-Host '=== git commit ==='
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { Write-Warning 'git not installed, skip commit' }
    else {
        # git writes LF/CRLF warnings to stderr; with Stop EAP PowerShell turns
        # that into an error, so relax EAP around native git calls.
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'SilentlyContinue'
        $targetsStr = ($Targets -join ',')
        git -C $repo add -A 2>&1 | Out-Null
        git -C $repo diff --cached --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host '  [SKIP] nothing to commit'
        } else {
            git -C $repo commit -m "sync: distribute to $targetsStr  $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | ForEach-Object { Write-Host "  $_" }
        }
        $ErrorActionPreference = $prevEAP
    }
}

Write-Host ''
Write-Host 'Done.'
