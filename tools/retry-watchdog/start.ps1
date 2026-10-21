param(
    [string]$Thread  = "<thread-uuid>",
    [int]$Interval   = 15,
    [int]$Stall      = 120,
    [string]$Prompt  = "",
    [string]$Model   = "",
    [string]$Effort  = "",
    [switch]$ExecFallback
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$log  = Join-Path $here "logs"
New-Item -ItemType Directory -Force -Path $log | Out-Null

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) { throw "python not found in PATH" }
$py = $pyCmd.Source

$argList = @(
    (Join-Path $here "watchdog.py"),
    "--thread", $Thread,
    "--interval", "$Interval",
    "--stall-seconds", "$Stall",
    "--log-dir", $log
)
if ($Prompt)       { $argList += @("--prompt", $Prompt) }
if ($Model)        { $argList += @("--model",  $Model) }
if ($Effort)       { $argList += @("--effort", $Effort) }
if ($ExecFallback) { $argList += @("--exec-fallback") }

$proc = Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $here `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $log "stdout.log") `
    -RedirectStandardError  (Join-Path $log "stderr.log")

$proc.Id | Set-Content (Join-Path $log "watcher.pid")
Write-Host "watchdog started"
Write-Host "  pid     : $($proc.Id)"
Write-Host "  thread  : $Thread"
Write-Host "  log     : $(Join-Path $log 'watchdog.log')"
Write-Host "  stop    : .\stop.ps1"
