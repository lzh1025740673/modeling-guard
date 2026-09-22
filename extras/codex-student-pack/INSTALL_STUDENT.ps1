param(
    [string]$TargetProject = (Join-Path (Split-Path $PSScriptRoot -Parent) 'math_modeling_project'),
    [switch]$VerifyOnly,
    [string]$PythonExe
)
$ErrorActionPreference = 'Stop'
try {
    $candidates = @()
    if ($PythonExe) {
        $candidates += @{ Exe = $PythonExe; Prefix = @() }
    } else {
        foreach ($name in @('py', 'python', 'python3')) {
            $found = Get-Command $name -ErrorAction SilentlyContinue
            if ($found) {
                $prefix = @()
                if ($name -eq 'py') { $prefix = @('-3') }
                $candidates += @{ Exe = $found.Source; Prefix = $prefix }
            }
        }
        $bundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (Test-Path -LiteralPath $bundled -PathType Leaf) {
            $candidates += @{ Exe = $bundled; Prefix = @() }
        }
    }
    $selected = $null
    foreach ($candidate in $candidates) {
        $executable = $candidate.Exe
        $prefixArgs = $candidate.Prefix
        try {
            & $executable @prefixArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { $selected = $candidate; break }
        } catch { }
    }
    if (-not $selected) { throw 'Python >=3.10 not found. Install Python manually and reopen this installer.' }
    $executable = $selected.Exe
    $prefixArgs = $selected.Prefix
    $arguments = @('-B', (Join-Path $PSScriptRoot 'installer\install_skill.py'), '--project', $TargetProject)
    if ($VerifyOnly) { $arguments += '--verify' }
    & $executable @prefixArgs @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host ('INSTALL_BLOCKED: ' + $_.Exception.Message)
    exit 1
}
