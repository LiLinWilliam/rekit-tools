<#
Frida dynamic-instrumentation environment and device-side frida-server binaries.

Creates venv\frida from the locked requirements, then fetches frida-server for
Android. Offline by default: the local uv cache must already hold the wheels.
#>
param(
    [switch]$Online,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$RK = Split-Path -Parent $PSScriptRoot
$runtime = Get-ChildItem -LiteralPath "$RK\toolchain\python" -Directory |
    Where-Object { $_.Name -like 'cpython-3.12.*-windows-x86_64-none' -and -not $_.LinkType } |
    Sort-Object Name | Select-Object -First 1
if (-not $runtime) { throw 'Local Python 3.12 runtime is missing.' }
$python = Join-Path $runtime.FullName 'python.exe'
$venv = Join-Path $RK 'venv\frida'
$venvPy = Join-Path $venv 'Scripts\python.exe'
$uv = Join-Path $RK 'bin\uv.exe'
$pins = Join-Path $RK 'requirements\frida.txt'
$tooling = Join-Path $RK 'tooling\frida'
$version = '17.24.0'

if ($Force -and (Test-Path -LiteralPath $venv)) { Remove-Item -LiteralPath $venv -Recurse -Force }
if (-not (Test-Path -LiteralPath $venvPy)) {
    Write-Host "Creating $venv"
    & $python -I -B -m venv --without-pip $venv
    if ($LASTEXITCODE) { throw "venv creation failed: $LASTEXITCODE" }
}

$install = @($uv, 'pip', 'install', '--python', $venvPy, '--no-deps', '-r', $pins)
if (-not $Online) { $install += '--offline' }
Write-Host ('Installing locked packages ' + $(if ($Online) { '(online)' } else { '(offline)' }))
& $install[0] $install[1..($install.Count - 1)]
if ($LASTEXITCODE) { throw "package install failed: $LASTEXITCODE" }
foreach ($dll in (Get-ChildItem -LiteralPath "$RK\toolchain\vcredist" -Filter '*.dll' -ErrorAction SilentlyContinue)) {
    Copy-Item -LiteralPath $dll.FullName -Destination (Join-Path $venv 'Scripts') -Force
}
& $uv pip check --python $venvPy
if ($LASTEXITCODE) { throw "dependency check failed: $LASTEXITCODE" }

New-Item -ItemType Directory -Force -Path $tooling | Out-Null
foreach ($abi in @('android-arm64', 'android-x86_64')) {
    $archive = Join-Path $tooling "frida-server-$version-$abi.xz"
    $binary = Join-Path $tooling "frida-server-$version-$abi"
    if (Test-Path -LiteralPath $binary) { Write-Host "Present $binary"; continue }
    if (-not (Test-Path -LiteralPath $archive)) {
        $url = "https://github.com/frida/frida/releases/download/$version/frida-server-$version-$abi.xz"
        Write-Host "Downloading $url"
        & curl.exe -sSL --fail --max-time 600 -o $archive $url
        if ($LASTEXITCODE) { throw "download failed for $abi : $LASTEXITCODE" }
    }
}
& $python -I -B -X utf8 (Join-Path $PSScriptRoot 'extract_xz.py') $tooling
if ($LASTEXITCODE) { throw "extraction failed: $LASTEXITCODE" }

& $venvPy -c "import frida,objection,frida_tools;print('frida',frida.__version__,'frida-tools',frida_tools.__version__,'objection',objection.__version__)"
if ($LASTEXITCODE) { throw "import check failed: $LASTEXITCODE" }
Write-Host 'Frida environment ready.'
