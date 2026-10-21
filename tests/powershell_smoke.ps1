$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files = @(Get-ChildItem (Join-Path $root 'tools') -Recurse -File -Filter '*.ps1')
if ($files.Count -eq 0) { throw 'No PowerShell tools found.' }

$parseFailures = @()
foreach ($file in $files) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName, [ref]$tokens, [ref]$parseErrors
    ) | Out-Null
    if ($parseErrors.Count) {
        $parseFailures += "$($file.FullName): $($parseErrors.Count) parse error(s)"
    }
}
if ($parseFailures.Count) {
    $parseFailures | ForEach-Object { Write-Error $_ }
    exit 1
}

$watchdogDir = Join-Path $root 'tools/retry-watchdog'
$smokeDir = Join-Path ([IO.Path]::GetTempPath()) "rekit-tools-ps-smoke-$PID"
New-Item -ItemType Directory -Force -Path $smokeDir | Out-Null
$started = $false
$global:stoppedPid = $null
try {
    function global:Start-Process {
        param(
            [string]$FilePath,
            [string[]]$ArgumentList,
            [string]$WorkingDirectory,
            [string]$WindowStyle,
            [switch]$PassThru,
            [string]$RedirectStandardOutput,
            [string]$RedirectStandardError
        )
        $global:capturedCommand = @($FilePath) + $ArgumentList
        [pscustomobject]@{ Id = 4242 }
    }
    $startOutput = (& (Join-Path $watchdogDir 'start.ps1') -Thread 'smoke-thread' -Interval 1 -Stall 2 -LogDir $smokeDir *>&1 | Out-String)
    if ($startOutput -notmatch 'watchdog started') {
        throw "start.ps1 smoke invocation failed (exit=$LASTEXITCODE; output=$startOutput)"
    }
    if (-not (Test-Path (Join-Path $smokeDir 'watcher.pid'))) {
        throw 'start.ps1 did not write watcher.pid.'
    }
    if ($global:capturedCommand[1] -ne (Join-Path $watchdogDir 'watchdog.py')) {
        throw 'start.ps1 built an unexpected watchdog command.'
    }
    $started = $true

    function global:Get-Process {
        param([int]$Id, [switch]$ErrorAction)
        [pscustomobject]@{ Id = $Id }
    }
    function global:Stop-Process {
        param([int]$Id, [switch]$Force)
        $global:stoppedPid = $Id
    }
    $stopOutput = (& (Join-Path $watchdogDir 'stop.ps1') -LogDir $smokeDir *>&1 | Out-String)
    if ($stopOutput -notmatch 'watchdog stopped: pid 4242') {
        throw "stop.ps1 smoke invocation failed (exit=$LASTEXITCODE; output=$stopOutput)"
    }
    if ($global:stoppedPid -ne 4242) { throw 'stop.ps1 did not stop the recorded PID.' }
    if (Test-Path (Join-Path $smokeDir 'watcher.pid')) {
        throw 'stop.ps1 left watcher.pid behind.'
    }
    Write-Host "PowerShell smoke passed: parsed $($files.Count) scripts; exercised watchdog start/stop."
} finally {
    Remove-Item Function:\Start-Process, Function:\Get-Process, Function:\Stop-Process -ErrorAction SilentlyContinue
    if ($started -and (Test-Path (Join-Path $smokeDir 'watcher.pid'))) {
        Remove-Item (Join-Path $smokeDir 'watcher.pid') -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $smokeDir -Recurse -Force -ErrorAction SilentlyContinue
}
