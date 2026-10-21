$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$log  = Join-Path $here "logs"
$pidFile = Join-Path $log "watcher.pid"
$lockFile = Join-Path $log "watchdog.lock"

$targets = @()
if (Test-Path $pidFile) {
    $targets += [int](Get-Content $pidFile | Select-Object -First 1)
}
if (Test-Path $lockFile) {
    $targets += [int](Get-Content $lockFile | Select-Object -First 1)
}
$targets = $targets | Sort-Object -Unique | Where-Object { $_ -gt 0 }

$stopped = @()
foreach ($procId in $targets) {
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($p) {
        Stop-Process -Id $procId -Force
        $stopped += $procId
    }
}
Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
if ($stopped.Count -gt 0) {
    Write-Host "watchdog stopped: pid $($stopped -join ', ')"
} else {
    Write-Host "no watchdog process running"
}
