param([switch]$NoOpen, [switch]$NoPause, [string]$PythonExe)
$ErrorActionPreference = 'Stop'
$exitStatus = 0
try {
    $runtimeCandidates = @()
    if ($PythonExe) { $runtimeCandidates += @{ Exe = $PythonExe; Prefix = @() } }
    else {
        foreach ($name in @('py', 'python', 'python3')) {
            $found = Get-Command $name -ErrorAction SilentlyContinue
            if ($found) {
                $prefixArgs = @()
                if ($name -eq 'py') { $prefixArgs = @('-3') }
                $runtimeCandidates += @{ Exe = $found.Source; Prefix = $prefixArgs }
            }
        }
        $codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (Test-Path -LiteralPath $codexPython) { $runtimeCandidates += @{ Exe = $codexPython; Prefix = @() } }
    }
    $chosen = $null
    foreach ($candidate in $runtimeCandidates) {
        $exe = $candidate.Exe
        $prefixArgs = $candidate.Prefix
        try {
            & $exe @prefixArgs -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)" 2>$null
            if ($LASTEXITCODE -eq 0) { $chosen = $candidate; break }
        } catch { }
    }
    if (-not $chosen) { throw 'Python 3.10+ not found. Install from python.org, then retry. Nothing has been installed or approved.' }
    $exe = $chosen.Exe
    $prefixArgs = $chosen.Prefix
    Push-Location -LiteralPath $PSScriptRoot
    try {
        $projectName = 'demo-project-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,6))
        Write-Host 'Modeling Guard - synthetic software demo only; no teacher approval of real student work.'
        & $exe @prefixArgs -m modeling_guard init $projectName
        if ($LASTEXITCODE -ne 0) { throw 'Demo initialization failed.' }
        & $exe @prefixArgs -m modeling_guard check $projectName
        if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
        & $exe @prefixArgs -m modeling_guard approve $projectName --teacher 'Synthetic demo fixture'
        if ($LASTEXITCODE -ne 0) { throw 'Demo approval failed.' }
        & $exe @prefixArgs -m modeling_guard run $projectName
        if ($LASTEXITCODE -ne 0) { throw 'Demo needs review. See the run report.' }
        $runsPath = Join-Path $projectName '.modeling_guard\runs'
        $reportFile = Get-ChildItem -LiteralPath $runsPath -Directory | ForEach-Object { Join-Path $_.FullName 'report.html' } | Select-Object -First 1
        if (-not (Test-Path -LiteralPath $reportFile)) { throw 'Report not found.' }
        Write-Host "DEMO_OK: $reportFile"
        if (-not $NoOpen) { Start-Process -FilePath $reportFile }
    } finally { Pop-Location }
} catch {
    Write-Host ('STOP: ' + $_.Exception.Message) -ForegroundColor Red
    $exitStatus = 2
}
if (-not $NoPause) { Read-Host 'Press Enter to close' | Out-Null }
exit $exitStatus
